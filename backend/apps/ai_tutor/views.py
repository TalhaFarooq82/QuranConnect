from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import TutorChat, TutorMessage, TutorShareLink, TutorUpload
from .services import ask_islamic_tutor


# ─────────────────────────────────────────────
# AI RESPONSE CLEANER
# ─────────────────────────────────────────────
def get_ai_answer(prompt, chat_history=None):
    """
    ask_islamic_tutor may return:
    1) plain string
    2) tuple like (answer, history)
    This always returns only the clean answer text.
    """
    if chat_history is None:
        chat_history = []

    result = ask_islamic_tutor(prompt, chat_history)

    if isinstance(result, tuple):
        return str(result[0]).strip()

    return str(result).strip()

def generate_chat_title(user_text):
    """
    Generate a clean 4-6 word sidebar title from the user's first message.
    Falls back to simple keyword cleanup if AI title generation fails.
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

        # Keep max 5 words
        words = title.split()
        title = " ".join(words[:5]).strip()

        if title:
            return title.title()

    except Exception:
        pass

    # Fallback if AI title generation fails
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
        "hi",
        "hello",
    ]

    text = user_text.lower()

    for phrase in remove_phrases:
        text = text.replace(phrase, " ")

    for ch in ["?", ".", ",", "!", ":", ";", '"', "'"]:
        text = text.replace(ch, "")

    stopwords = {
        "the", "a", "an", "and", "or", "but", "to", "of", "in", "on",
        "for", "with", "about", "me", "my", "is", "are", "was", "were",
        "do", "does", "did", "be", "it", "this", "that", "please", "you",
        "i", "am", "can", "could", "should", "would"
    }

    words = [w for w in text.split() if w not in stopwords]
    title = " ".join(words[:5]).strip()

    return title.title() if title else "New Chat"

    # Remove common question starters
    remove_phrases = [
        "can you tell me",
        "could you tell me",
        "please tell me",
        "tell me",
        "how to",
        "how do i",
        "what is",
        "what are",
        "explain",
        "give me",
        "i want to know",
        "hi,",
        "hello,",
    ]

    lowered = text.lower()

    for phrase in remove_phrases:
        if lowered.startswith(phrase):
            text = text[len(phrase):].strip(" ?.,")
            break

    # Clean symbols
    for ch in ["?", ".", ",", "!", ":", ";", '"', "'"]:
        text = text.replace(ch, "")

    words = text.split()

    # Remove small filler words
    stopwords = {
        "the", "a", "an", "and", "or", "but", "to", "of", "in", "on",
        "for", "with", "about", "me", "my", "is", "are", "was", "were",
        "do", "does", "did", "be", "it", "this", "that", "please"
    }

    clean_words = [w for w in words if w.lower() not in stopwords]

    if not clean_words:
        clean_words = words

    title_words = clean_words[:5]

    title = " ".join(title_words).strip()

    if not title:
        title = "New Chat"

    return title.title()


def _safe_redirect(request, fallback_name="ai_tutor_home", **fallback_kwargs):
    """
    Safe redirect helper for normal form posts.
    """
    nxt = request.POST.get("next") or request.GET.get("next")
    if nxt:
        return redirect(nxt)

    ref = request.META.get("HTTP_REFERER")
    if ref:
        return redirect(ref)

    return redirect(fallback_name, **fallback_kwargs)


def _get_next_active_chat(user, exclude_id=None):
    qs = TutorChat.objects.filter(user=user, is_archived=False)

    if exclude_id:
        qs = qs.exclude(id=exclude_id)

    return qs.order_by("-updated_at").first()


def _json_or_redirect(request, redirect_url):
    """
    If frontend uses fetch(), return JSON.
    If normal form submit, redirect normally.
    """
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "ok": True,
            "redirect_url": redirect_url,
        })

    return redirect(redirect_url)


# ─────────────────────────────────────────────
# HOME / NEW CHAT
# ─────────────────────────────────────────────
@login_required
def chat_home(request):
    """
    AI Tutor home opens the latest active chat.
    It creates a new chat only if no active chat exists.
    """
    chat = _get_next_active_chat(request.user)

    if chat:
        return redirect("ai_tutor_chat", chat_id=chat.id)

    chat = TutorChat.objects.create(user=request.user, title="New Chat")
    return redirect("ai_tutor_chat", chat_id=chat.id)


@login_required
def new_chat(request):
    """
    Use this for the New Conversation button.
    """
    chat = TutorChat.objects.create(user=request.user, title="New Chat")
    return redirect("ai_tutor_chat", chat_id=chat.id)


# ─────────────────────────────────────────────
# MAIN CHAT PAGE
# ─────────────────────────────────────────────
@login_required
def chat_page(request, chat_id):
    """
    Main AI Tutor chat page.
    If chat does not exist, redirect safely to latest active chat/home.
    """
    try:
        chat = TutorChat.objects.get(id=chat_id, user=request.user)
    except TutorChat.DoesNotExist:
        next_chat = _get_next_active_chat(request.user)
        if next_chat:
            return redirect("ai_tutor_chat", chat_id=next_chat.id)
        return redirect("ai_tutor_home")

    q = request.GET.get("q", "").strip()
    show_archived = request.GET.get("archived") == "1"

    chats_qs = TutorChat.objects.filter(user=request.user)

    if show_archived:
        chats_qs = chats_qs.filter(is_archived=True)
    else:
        chats_qs = chats_qs.filter(is_archived=False)

    if q:
        chats_qs = chats_qs.filter(title__icontains=q)

    chats = chats_qs.order_by("-updated_at")[:100]

    if request.method == "POST":
        user_text = request.POST.get("message", "").strip()

        if user_text:
            TutorMessage.objects.create(
                chat=chat,
                role="user",
                content=user_text
            )
            chat.save()

            # Optional document context from uploaded files
            doc_context = "\n\n".join(
                chat.uploads.exclude(extracted_text="")
                .values_list("extracted_text", flat=True)[:3]
            )

            prompt = user_text

            if doc_context:
                prompt = (
                    f"User question:\n{user_text}\n\n"
                    f"Use this document context if relevant:\n{doc_context}"
                )

            # Build clean chat history
            chat_history = []
            for msg in chat.messages.order_by("created_at"):
                chat_history.append({
                    "role": msg.role,
                    "content": msg.content
                })

            assistant_text = get_ai_answer(prompt, chat_history)

            # Auto-title from first real user message
            if chat.title == "New Chat":
                chat.title = generate_chat_title(user_text)
                chat.save()

            TutorMessage.objects.create(
                chat=chat,
                role="assistant",
                content=assistant_text
            )
            chat.save()

            return redirect("ai_tutor_chat", chat_id=chat.id)

    messages = chat.messages.order_by("created_at")

    return render(request, "ai_tutor/chat_page.html", {
        "active_chat": chat,
        "chats": chats,
        "messages": messages,
        "search_q": q,
        "show_archived": show_archived,
    })


# ─────────────────────────────────────────────
# CHAT ACTIONS: RENAME / DELETE / ARCHIVE / SHARE
# ─────────────────────────────────────────────
@require_POST
@login_required
def rename_chat(request, chat_id):
    chat = get_object_or_404(TutorChat, id=chat_id, user=request.user)

    title = (request.POST.get("title") or "").strip()[:120]

    if title:
        chat.title = title
        chat.save()

    return _safe_redirect(request, "ai_tutor_chat", chat_id=chat.id)


@require_POST
@login_required
def delete_chat(request, chat_id):
    chat = get_object_or_404(TutorChat, id=chat_id, user=request.user)

    chat.delete()

    next_chat = _get_next_active_chat(request.user)

    if next_chat:
        redirect_url = reverse("ai_tutor_chat", args=[next_chat.id])
    else:
        redirect_url = reverse("ai_tutor_home")

    return _json_or_redirect(request, redirect_url)


@require_POST
@login_required
def archive_chat(request, chat_id):
    chat = get_object_or_404(TutorChat, id=chat_id, user=request.user)

    chat.is_archived = True
    chat.save()

    next_chat = _get_next_active_chat(request.user, exclude_id=chat.id)

    if next_chat:
        redirect_url = reverse("ai_tutor_chat", args=[next_chat.id])
    else:
        redirect_url = reverse("ai_tutor_home")

    return _json_or_redirect(request, redirect_url)


@require_POST
@login_required
def unarchive_chat(request, chat_id):
    chat = get_object_or_404(TutorChat, id=chat_id, user=request.user)

    chat.is_archived = False
    chat.save()

    redirect_url = reverse("ai_tutor_chat", args=[chat.id])
    return _json_or_redirect(request, redirect_url)


@require_POST
@login_required
def share_chat(request, chat_id):
    chat = get_object_or_404(TutorChat, id=chat_id, user=request.user)

    link = TutorShareLink.objects.create(chat=chat)

    share_url = request.build_absolute_uri(
        reverse("ai_tutor_shared_view", args=[str(link.token)])
    )

    return JsonResponse({
        "ok": True,
        "url": share_url
    })


def shared_chat_view(request, token):
    link = get_object_or_404(TutorShareLink, token=token, is_active=True)

    chat = link.chat
    messages = chat.messages.order_by("created_at")

    return render(request, "ai_tutor/shared_chat.html", {
        "chat": chat,
        "messages": messages,
    })


# ─────────────────────────────────────────────
# MESSAGE ACTIONS
# ─────────────────────────────────────────────

def _require_owner(msg_id, user):
    msg = get_object_or_404(TutorMessage, id=msg_id)

    if msg.chat.user != user:
        return None

    return msg


def _build_chat_history(chat):
    history = []

    for old_msg in chat.messages.order_by("created_at"):
        history.append({
            "role": old_msg.role,
            "content": old_msg.content
        })

    return history


def _run_action_as_user_prompt(msg, user_prompt, ai_prompt):
    """
    Saves the clicked action as a visible user message,
    then saves the AI response under it.
    """
    chat = msg.chat

    TutorMessage.objects.create(
        chat=chat,
        role="user",
        content=user_prompt
    )

    chat_history = _build_chat_history(chat)

    ai_response = get_ai_answer(ai_prompt, chat_history)

    TutorMessage.objects.create(
        chat=chat,
        role="assistant",
        content=ai_response
    )

    chat.save()

    return JsonResponse({"ok": True})


@require_POST
@login_required
def regenerate_answer(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if not msg or msg.role != "assistant":
        return HttpResponseForbidden("Not allowed")

    last_user = msg.chat.messages.filter(role="user").order_by("-created_at").first()

    if not last_user:
        return JsonResponse({"error": "No user prompt found"}, status=400)

    user_prompt = "Regenerate this answer"

    ai_prompt = (
        "Regenerate the previous answer in a clearer and better way. "
        "Only return the improved answer. Do not include tuples, brackets, "
        "chat history, source dictionaries, or role labels.\n\n"
        f"Original user question:\n{last_user.content}\n\n"
        f"Previous answer:\n{msg.content}"
    )

    return _run_action_as_user_prompt(msg, user_prompt, ai_prompt)


@require_POST
@login_required
def make_shorter(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if not msg or msg.role != "assistant":
        return HttpResponseForbidden("Not allowed")

    user_prompt = "Make this answer shorter"

    ai_prompt = (
        "Rewrite the following answer in a shorter, cleaner way. "
        "Only return the improved answer. Do not include tuples, brackets, "
        "chat history, source dictionaries, or role labels.\n\n"
        f"{msg.content}"
    )

    return _run_action_as_user_prompt(msg, user_prompt, ai_prompt)


@require_POST
@login_required
def make_easier(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if not msg or msg.role != "assistant":
        return HttpResponseForbidden("Not allowed")

    user_prompt = "Make this answer easier"

    ai_prompt = (
        "Rewrite the following answer in simple and easy words. "
        "Only return the improved answer. Do not include tuples, brackets, "
        "chat history, source dictionaries, or role labels.\n\n"
        f"{msg.content}"
    )

    return _run_action_as_user_prompt(msg, user_prompt, ai_prompt)


@require_POST
@login_required
def save_answer(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if not msg or msg.role != "assistant":
        return HttpResponseForbidden("Not allowed")

    msg.saved = True
    msg.save()

    TutorMessage.objects.create(
        chat=msg.chat,
        role="user",
        content="Save this answer"
    )

    TutorMessage.objects.create(
        chat=msg.chat,
        role="assistant",
        content="Saved. You can find this answer in your saved responses."
    )

    msg.chat.save()

    return JsonResponse({"ok": True})


@require_POST
@login_required
def generate_quiz(request, msg_id):
    msg = _require_owner(msg_id, request.user)

    if not msg or msg.role != "assistant":
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
        "- Do not include tuples, brackets, chat history, source dictionaries, or role labels.\n\n"
        f"{msg.content}"
    )

    return _run_action_as_user_prompt(msg, user_prompt, ai_prompt)


# ─────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────
@login_required
@require_POST
def upload_file(request, chat_id):
    chat = get_object_or_404(TutorChat, id=chat_id, user=request.user)

    f = request.FILES.get("file")

    if not f:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    upload = TutorUpload.objects.create(
        user=request.user,
        chat=chat,
        file=f,
        filename=f.name,
        extracted_text=""
    )

    text = ""
    name_lower = f.name.lower()

    try:
        if name_lower.endswith(".txt"):
            text = f.read().decode("utf-8", errors="ignore")

        elif name_lower.endswith(".docx"):
            import docx

            doc = docx.Document(upload.file.path)
            text = "\n".join([p.text for p in doc.paragraphs])

        elif name_lower.endswith(".pdf"):
            import PyPDF2

            with open(upload.file.path, "rb") as fp:
                reader = PyPDF2.PdfReader(fp)
                pages = []

                for page in reader.pages[:20]:
                    pages.append(page.extract_text() or "")

                text = "\n".join(pages)

        else:
            return JsonResponse({
                "error": "Only PDF, TXT, and DOCX files are supported."
            }, status=400)

    except Exception as e:
        return JsonResponse({
            "error": f"Could not read file: {str(e)}"
        }, status=400)

    upload.extracted_text = text[:200000]
    upload.save()
    chat.save()

    return JsonResponse({
        "ok": True,
        "filename": upload.filename
    })