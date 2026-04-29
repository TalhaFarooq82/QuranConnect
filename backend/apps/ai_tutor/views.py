from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.ai_tutor.services import ask_islamic_tutor
from django.http import JsonResponse
from apps.ai_tutor.models import ChatMessage, ChatSession

@login_required
def chat_page(request, session_id=None):
    # Get all user sessions for sidebar
    all_sessions = ChatSession.objects.filter(
        user=request.user
    ).order_by('-created_at')

    if request.method == "GET":
        # If session_id given → load that session
        # Otherwise → create new session
        if session_id:
            try:
                session = ChatSession.objects.get(
                    id=session_id,
                    user=request.user
                )
            except ChatSession.DoesNotExist:
                return redirect('chat_page')
        else:
            session = ChatSession.objects.create(user=request.user)
            return redirect('chat_session', session_id=session.id)

        messages = ChatMessage.objects.filter(session=session)

        return render(request, 'ai_tutor/chat_page.html', {
            'session':      session,
            'messages':     messages,
            'all_sessions': all_sessions,
        })

    if request.method == "POST":
        question   = request.POST['question']
        session_id = request.POST['session_id']
        session    = ChatSession.objects.get(id=session_id, user=request.user)

        # Auto title from first question
        if not session.title:
            session.title = question[:50]
            session.save()

        previous_messages = ChatMessage.objects.filter(session=session)
        chat_history = []
        for msg in previous_messages:
            chat_history.append({"role": "user",      "content": msg.question})
            chat_history.append({"role": "assistant", "content": msg.answer})

        answer, _ = ask_islamic_tutor(question, chat_history)

        ChatMessage.objects.create(
            session  = session,
            question = question,
            answer   = answer
        )

        return JsonResponse({'answer': answer})


@login_required
def new_chat(request):
    session = ChatSession.objects.create(user=request.user)
    return redirect('chat_session', session_id=session.id)


@login_required  
def delete_session(request, session_id):
    ChatSession.objects.filter(
        id=session_id,
        user=request.user
    ).delete()
    return redirect('chat_page')