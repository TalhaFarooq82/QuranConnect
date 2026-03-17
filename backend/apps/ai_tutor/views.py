from django.shortcuts import render,  redirect
from django.contrib.auth.decorators import login_required
from apps.ai_tutor.services import ask_islamic_tutor
from django.http import JsonResponse
from apps.ai_tutor.models import ChatMessage, ChatSession
# Create your views here.

@login_required
def chat_page(request):
    if request.method == "GET":
        session, created = ChatSession.objects.get_or_create( user = request.user)
        messages = ChatMessage.objects.filter(session=session)
    
        return render(request, 'ai_tutor/chat_page.html', {'session': session, 'messages': messages})


    if request.method == "POST":
        question = request.POST['question']
        session_id = request.POST['session_id']
        session = ChatSession.objects.get(id=session_id)

        previous_messages = ChatMessage.objects.filter(session=session)
        chat_history = []
        for msg in previous_messages:
            chat_history.append({"role": "user",      "content": msg.question})
            chat_history.append({"role": "assistant",  "content": msg.answer})

        answer, _ = ask_islamic_tutor(question, chat_history)  

        ChatMessage.objects.create(
            session  = session,   
            question = question,   
            answer   = answer   
        )

        return JsonResponse({'answer': answer})
