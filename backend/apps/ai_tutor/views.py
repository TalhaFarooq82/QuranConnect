from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import TutorChat, TutorMessage, TutorShareLink, TutorUpload
from .services import ask_islamic_tutor


ALLOWED_UPLOAD_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
MAX_EXTRACTED_TEXT_LENGTH = 200_000
MAX_DOCUMENT_CONTEXT_LENGTH = 30_000


# ─────────────────────────────────────────────
# AI RESPONSE CLEANER
# ─────────────────────────────────────────────
def get_ai_answer(prompt, chat_history=None):
    """
    Return clean text from the AI tutor service.

    ask_islamic_tutor may return either a plain string or a tuple
    containing the answer and updated chat history.
    """
    if chat_history is None:
        chat_history = []

    result = ask_islamic_tutor(prompt, chat_history)

    if isinstance(result, tuple):
        if not result:
            raise ValueError("AI tutor returned an invalid response.")

        result = result[0]

    if result is None:
        raise ValueError("AI tutor returned an empty response.")

    answer = str(result).strip()

    if not answer:
        raise ValueError("AI tutor returned an empty response.")

    return answer


def generate_chat_title(user_text):
    """
    Generate a short sidebar title from the user's first message.

    AI title generation is attempted first. A local text-cleaning
    fallback is used when title generation fails.
    """
    user_text = user_text.strip()

    if not user_text:
        return "New Chat"

    title_prompt = (
        "Create a short chat title from this user message.\n"
        "Rules:\n"
        "- Maximum 5 words\n"
        "- No punctuation\n"
        "- No quotation marks\n"
        "- Do not answer the question\n"
        "- Only return the title\n\n"
        f"User message: {user_text}"
    )

    try:
        title = get_ai_answer(title_prompt)
        title = title.replace('"', "").replace("'", "").strip()
        title = " ".join(title.split()[:5]).strip()

        if title:
            return title.title()

    except Exception:
        pass

    remove_phrases = [
        "can you tell me",
        "could you tell me",
        "please tell me",
        "tell me",
        "how can i",
        "how i can",
        "how to",
        "how do i",
        "what is",
        "what are",
        "explain",
        "give me",
        "i want to know",
        "i am a student",
        "i am student",
        "i am in uni",
        "i am in university",
        "hello",
        "hi",
    ]

    text = user_text.lower().strip()

    for phrase in remove_phrases:
        if text.startswith(phrase):
            text = text[len(phrase):].strip(" ?.,!;:")
            break

    for character in ["?", ".", ",", "!", ":", ";", '"', "'"]:
        text = text.replace(character, "")

    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "but",
        "to",
        "of",
        "in",
        "on",
        "for",
        "with",
        "about",
        "me",
        "my",
        "is",
        "are",
        "was",
        "were",
        "do",
        "does",
        "did",
        "be",
        "it",
        "this",
        "that",
        "please",
        "you",
        "i",
        "am",
        "can",
        "could",
        "should",
        "would",
    }

    words = [
        word
        for word in text.split()
        if word not in stopwords
    ]

    title = " ".join(words[:5]).strip()

    return title.title() if title else "New Chat"


# ─────────────────────────────────────────────
# GENERAL HELPERS
# ─────────────────────────────────────────────
def _is_safe_redirect_url(request, url):
    """
    Return True when a redirect URL belongs to the current application.
    """
    if not url:
        return False

    return url_has_allowed_host_and_scheme(
        url=url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    )


def _safe_redirect(request, fallback_name="ai_tutor_home", **fallback_kwargs):
    """
    Redirect to a validated local destination or to the fallback route.
    """
    redirect_candidates = [
        request.POST.get("next"),
        request.GET.get("next"),
        request.META.get("HTTP_REFERER"),
    ]

    for target in redirect_candidates:
        if _is_safe_redirect_url(request, target):
            return redirect(target)

    return redirect(fallback_name, **fallback_kwargs)


def _get_next_active_chat(user, exclude_id=None):
    queryset = TutorChat.objects.filter(
        user=user,
        is_archived=False,
    )

    if exclude_id is not None:
        queryset = queryset.exclude(id=exclude_id)

    return queryset.order_by("-updated_at").first()


def _json_or_redirect(request, redirect_url):
    """
    Return JSON for AJAX requests and a normal redirect otherwise.
    """
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "redirect_url": redirect_url,
        })

    return redirect(redirect_url)


def _build_chat_history(chat, exclude_message_id=None):
    """
    Build ordered chat history from saved tutor messages.

    The current user message can be excluded because the AI service
    appends the current prompt itself.
    """
    messages = chat.messages.order_by("created_at")

    if exclude_message_id is not None:
        messages = messages.exclude(id=exclude_message_id)

    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]


def _require_owner(msg_id, user):
    """
    Return a message only when it belongs to the current user.
    """
    return get_object_or_404(
        TutorMessage,
        id=msg_id,
        chat__user=user,
    )


# ─────────────────────────────────────────────
# HOME / NEW CHAT
# ─────────────────────────────────────────────
@login_required
def chat_home(request):
    """
    Open the latest active chat.

    A new chat is created only when the user has no active chats.
    """
    chat = _get_next_active_chat(request.user)

    if chat:
        return redirect("ai_tutor_chat", chat_id=chat.id)

    chat = TutorChat.objects.create(
        user=request.user,
        title="New Chat",
    )

    return redirect("ai_tutor_chat", chat_id=chat.id)


@login_required
def new_chat(request):
    """
    Create a new AI Tutor conversation.
    """
    chat = TutorChat.objects.create(
        user=request.user,
        title="New Chat",
    )

    return redirect("ai_tutor_chat", chat_id=chat.id)


# ─────────────────────────────────────────────
# MAIN CHAT PAGE
# ─────────────────────────────────────────────
@login_required
def chat_page(request, chat_id):
    """
    Display and process the main AI Tutor chat page.
    """
    try:
        chat = TutorChat.objects.get(
            id=chat_id,
            user=request.user,
        )
    except TutorChat.DoesNotExist:
        next_chat = _get_next_active_chat(request.user)

        if next_chat:
            return redirect(
                "ai_tutor_chat",
                chat_id=next_chat.id,
            )

        return redirect("ai_tutor_home")

    search_query = request.GET.get("q", "").strip()
    show_archived = request.GET.get("archived") == "1"

    chats_queryset = TutorChat.objects.filter(
        user=request.user,
    )

    if show_archived:
        chats_queryset = chats_queryset.filter(
            is_archived=True,
        )
    else:
        chats_queryset = chats_queryset.filter(
            is_archived=False,
        )

    if search_query:
        chats_queryset = chats_queryset.filter(
            title__icontains=search_query,
        )

    chats = chats_queryset.order_by("-updated_at")[:100]

    if request.method == "POST":
        user_text = request.POST.get("message", "").strip()

        if user_text:
            user_message = TutorMessage.objects.create(
                chat=chat,
                role="user",
                content=user_text,
            )

            chat.save()

            document_texts = (
                chat.uploads
                .exclude(extracted_text="")
                .values_list("extracted_text", flat=True)[:3]
            )

            document_context = "\n\n".join(
                document_texts
            )[:MAX_DOCUMENT_CONTEXT_LENGTH]

            prompt = user_text

            if document_context:
                prompt = (
                    f"User question:\n{user_text}\n\n"
                    "Use this document context if relevant:\n"
                    f"{document_context}"
                )

            # Exclude the current message because ask_islamic_tutor
            # appends the current prompt to the history itself.
            chat_history = _build_chat_history(
                chat,
                exclude_message_id=user_message.id,
            )

            assistant_text = get_ai_answer(
                prompt,
                chat_history,
            )

            if chat.title == "New Chat":
                chat.title = generate_chat_title(user_text)
                chat.save()

            TutorMessage.objects.create(
                chat=chat,
                role="assistant",
                content=assistant_text,
            )

            chat.save()

            return redirect(
                "ai_tutor_chat",
                chat_id=chat.id,
            )

    messages = chat.messages.order_by("created_at")

    return render(
        request,
        "ai_tutor/chat_page.html",
        {
            "active_chat": chat,
            "chats": chats,
            "messages": messages,
            "search_q": search_query,
            "show_archived": show_archived,
        },
    )


# ─────────────────────────────────────────────
# CHAT ACTIONS
# ─────────────────────────────────────────────
@require_POST
@login_required
def rename_chat(request, chat_id):
    chat = get_object_or_404(
        TutorChat,
        id=chat_id,
        user=request.user,
    )

    title = (request.POST.get("title") or "").strip()[:120]

    if title:
        chat.title = title
        chat.save(update_fields=["title", "updated_at"])

    return _safe_redirect(
        request,
        "ai_tutor_chat",
        chat_id=chat.id,
    )


@require_POST
@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(
        TutorChat,
        id=chat_id,
        user=request.user,
    )

    chat.delete()

    next_chat = _get_next_active_chat(request.user)

    if next_chat:
        redirect_url = reverse(
            "ai_tutor_chat",
            args=[next_chat.id],
        )
    else:
        redirect_url = reverse("ai_tutor_home")

    return _json_or_redirect(
        request,
        redirect_url,
    )


@require_POST
@login_required
def archive_chat(request, chat_id):
    chat = get_object_or_404(
        TutorChat,
        id=chat_id,
        user=request.user,
    )

    chat.is_archived = True
    chat.save(update_fields=["is_archived", "updated_at"])

    next_chat = _get_next_active_chat(
        request.user,
        exclude_id=chat.id,
    )

    if next_chat:
        redirect_url = reverse(
            "ai_tutor_chat",
            args=[next_chat.id],
        )
    else:
        redirect_url = reverse("ai_tutor_home")

    return _json_or_redirect(
        request,
        redirect_url,
    )


@require_POST
@login_required
def unarchive_chat(request, chat_id):
    chat = get_object_or_404(
        TutorChat,
        id=chat_id,
        user=request.user,
    )

    chat.is_archived = False
    chat.save(update_fields=["is_archived", "updated_at"])

    redirect_url = reverse(
        "ai_tutor_chat",
        args=[chat.id],
    )

    return _json_or_redirect(
        request,
        redirect_url,
    )


@require_POST
@login_required
def share_chat(request, chat_id):
    chat = get_object_or_404(
        TutorChat,
        id=chat_id,
        user=request.user,
    )

    link = TutorShareLink.objects.create(chat=chat)

    share_url = request.build_absolute_uri(
        reverse(
            "ai_tutor_shared_view",
            args=[str(link.token)],
        )
    )

    return JsonResponse({
        "ok": True,
        "url": share_url,
    })


def shared_chat_view(request, token):
    link = get_object_or_404(
        TutorShareLink,
        token=token,
        is_active=True,
    )

    chat = link.chat
    messages = chat.messages.order_by("created_at")

    return render(
        request,
        "ai_tutor/shared_chat.html",
        {
            "chat": chat,
            "messages": messages,
        },
    )


# ─────────────────────────────────────────────
# MESSAGE ACTION HELPERS
# ─────────────────────────────────────────────
def _run_action_as_user_prompt(msg, user_prompt, ai_prompt):
    """
    Save an action as a visible user message and then save its AI response.
    """
    chat = msg.chat

    action_message = TutorMessage.objects.create(
        chat=chat,
        role="user",
        content=user_prompt,
    )

    chat_history = _build_chat_history(
        chat,
        exclude_message_id=action_message.id,
    )

    ai_response = get_ai_answer(
        ai_prompt,
        chat_history,
    )

    TutorMessage.objects.create(
        chat=chat,
        role="assistant",
        content=ai_response,
    )

    chat.save()

    return JsonResponse({"ok": True})


# ─────────────────────────────────────────────
# MESSAGE ACTIONS
# ─────────────────────────────────────────────
@require_POST
@login_required
def regenerate_answer(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if msg.role != "assistant":
        return HttpResponseForbidden("Not allowed")

    last_user = (
        msg.chat.messages
        .filter(role="user")
        .order_by("-created_at")
        .first()
    )

    if not last_user:
        return JsonResponse(
            {"error": "No user prompt found."},
            status=400,
        )

    user_prompt = "Regenerate this answer"

    ai_prompt = (
        "Regenerate the previous answer in a clearer and better way. "
        "Only return the improved answer. Do not include tuples, brackets, "
        "chat history, source dictionaries, or role labels.\n\n"
        f"Original user question:\n{last_user.content}\n\n"
        f"Previous answer:\n{msg.content}"
    )

    return _run_action_as_user_prompt(
        msg,
        user_prompt,
        ai_prompt,
    )


@require_POST
@login_required
def make_shorter(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if msg.role != "assistant":
        return HttpResponseForbidden("Not allowed")

    user_prompt = "Make this answer shorter"

    ai_prompt = (
        "Rewrite the following answer in a shorter, cleaner way. "
        "Only return the improved answer. Do not include tuples, brackets, "
        "chat history, source dictionaries, or role labels.\n\n"
        f"{msg.content}"
    )

    return _run_action_as_user_prompt(
        msg,
        user_prompt,
        ai_prompt,
    )


@require_POST
@login_required
def make_easier(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if msg.role != "assistant":
        return HttpResponseForbidden("Not allowed")

    user_prompt = "Make this answer easier"

    ai_prompt = (
        "Rewrite the following answer in simple and easy words. "
        "Only return the improved answer. Do not include tuples, brackets, "
        "chat history, source dictionaries, or role labels.\n\n"
        f"{msg.content}"
    )

    return _run_action_as_user_prompt(
        msg,
        user_prompt,
        ai_prompt,
    )


@require_POST
@login_required
def save_answer(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if msg.role != "assistant":
        return HttpResponseForbidden("Not allowed")

    if msg.saved:
        return JsonResponse({
            "ok": True,
            "already_saved": True,
        })

    msg.saved = True
    msg.save(update_fields=["saved"])

    TutorMessage.objects.create(
        chat=msg.chat,
        role="user",
        content="Save this answer",
    )

    TutorMessage.objects.create(
        chat=msg.chat,
        role="assistant",
        content=(
            "Saved. You can find this answer "
            "in your saved responses."
        ),
    )

    msg.chat.save()

    return JsonResponse({
        "ok": True,
        "already_saved": False,
    })


@require_POST
@login_required
def generate_quiz(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if msg.role != "assistant":
        return HttpResponseForbidden("Not allowed")

    user_prompt = "Generate quiz from this answer"

    ai_prompt = (
        "Create a clean quiz from the following answer.\n\n"
        "Format it exactly like this:\n"
        "1. MCQs\n"
        "2. Short Questions\n"
        "3. True/False\n\n"
        "Rules:\n"
        "- Include correct answers for MCQs and True/False.\n"
        "- Keep the quiz easy to read.\n"
        "- Only return the quiz.\n"
        "- Do not include tuples, brackets, chat history, "
        "source dictionaries, or role labels.\n\n"
        f"{msg.content}"
    )

    return _run_action_as_user_prompt(
        msg,
        user_prompt,
        ai_prompt,
    )


# ─────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────
@login_required
@require_POST
def upload_file(request, chat_id):
    chat = get_object_or_404(
        TutorChat,
        id=chat_id,
        user=request.user,
    )

    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return JsonResponse(
            {"error": "No file uploaded."},
            status=400,
        )

    filename = Path(uploaded_file.name).name[:255]
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        return JsonResponse(
            {
                "error": (
                    "Only PDF, TXT, and DOCX files are supported."
                )
            },
            status=400,
        )

    if uploaded_file.size > MAX_UPLOAD_SIZE:
        return JsonResponse(
            {
                "error": (
                    "The uploaded file must be 10 MB or smaller."
                )
            },
            status=400,
        )

    upload = None

    try:
        upload = TutorUpload.objects.create(
            user=request.user,
            chat=chat,
            file=uploaded_file,
            filename=filename,
            extracted_text="",
        )

        if extension == ".txt":
            with upload.file.open("rb") as file_pointer:
                text = file_pointer.read().decode(
                    "utf-8",
                    errors="ignore",
                )

        elif extension == ".docx":
            import docx

            with upload.file.open("rb") as file_pointer:
                document = docx.Document(file_pointer)

            text = "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

        else:
            import PyPDF2

            with upload.file.open("rb") as file_pointer:
                reader = PyPDF2.PdfReader(file_pointer)

                pages = [
                    page.extract_text() or ""
                    for page in reader.pages[:20]
                ]

            text = "\n".join(pages)

        upload.extracted_text = text[:MAX_EXTRACTED_TEXT_LENGTH]
        upload.save(update_fields=["extracted_text"])

        chat.save()

        return JsonResponse({
            "ok": True,
            "filename": upload.filename,
        })

    except Exception:
        if upload is not None:
            upload.file.delete(save=False)
            upload.delete()

        return JsonResponse(
            {
                "error": (
                    "The uploaded file could not be read."
                )
            },
            status=400,
        )