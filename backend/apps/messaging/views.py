from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from apps.bookings.models import Conversation, Message
from .models import SharedFile
import os


@login_required
def inbox(request):
    user = request.user

    # Get all conversations this user is part of
    if user.role == 'student':
        conversations = Conversation.objects.filter(
            student=user
        ).select_related('job', 'teacher').order_by('-created_at')
    else:
        conversations = Conversation.objects.filter(
            teacher=user
        ).select_related('job', 'student').order_by('-created_at')

    # Attach last message to each conversation
    conversation_list = []
    for conv in conversations:
        last_msg = conv.messages.order_by('-created_at').first()
        other_user = conv.teacher if user == conv.student else conv.student
        conversation_list.append({
            'conversation': conv,
            'last_message': last_msg,
            'other_user': other_user,
        })

    return render(request, 'messaging/inbox.html', {
        'conversation_list': conversation_list,
    })

from itertools import chain
from operator import attrgetter

@login_required
def chat_room(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    user = request.user

    if user != conversation.student and user != conversation.teacher:
        return redirect('inbox')

    other_user = conversation.teacher if user == conversation.student else conversation.student

    # Load text messages
    text_messages = conversation.messages.select_related('sender').order_by('created_at')

    # Load shared files
    shared_files = conversation.shared_files.select_related('uploaded_by').order_by('uploaded_at')

    # Tag each item so template knows what type it is
    tagged_messages = []
    for msg in text_messages:
        tagged_messages.append({
            'type': 'text',
            'sender': msg.sender,
            'body': msg.body,
            'timestamp': msg.created_at,
        })
    for f in shared_files:
        tagged_messages.append({
            'type': f.file_type,
            'sender': f.uploaded_by,
            'file_url': f.file.url,
            'original_name': f.original_name,
            'timestamp': f.uploaded_at,
        })

    # Sort everything by timestamp together
    tagged_messages.sort(key=lambda x: x['timestamp'])

    # Mark notifications as read
    user.notifications.filter(type='message', is_read=False).update(is_read=True)

    # Sidebar conversations
    if user.role == 'student':
        conversations = Conversation.objects.filter(
            student=user
        ).select_related('job', 'teacher').order_by('-created_at')
    else:
        conversations = Conversation.objects.filter(
            teacher=user
        ).select_related('job', 'student').order_by('-created_at')

    conversation_list = []
    for conv in conversations:
        last_msg = conv.messages.order_by('-created_at').first()
        other = conv.teacher if user == conv.student else conv.student
        conversation_list.append({
            'conversation': conv,
            'last_message': last_msg,
            'other_user': other,
        })

    return render(request, 'messaging/chat_room.html', {
        'conversation': conversation,
        'other_user': other_user,
        'tagged_messages': tagged_messages,
        'conversation_list': conversation_list,
    })


@login_required
def upload_file(request, conversation_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    conversation = get_object_or_404(Conversation, id=conversation_id)
    user = request.user

    if user != conversation.student and user != conversation.teacher:
        return JsonResponse({'error': 'Not allowed'}, status=403)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'error': 'No file'}, status=400)

    # Detect file type
    name = uploaded_file.name.lower()
    if name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
        file_type = 'image'
    elif name.endswith('.pdf'):
        file_type = 'pdf'
    elif name.endswith(('.doc', '.docx')):
        file_type = 'doc'
    elif name.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
        file_type = 'audio'
    else:
        return JsonResponse({'error': 'File type not allowed'}, status=400)

    shared_file = SharedFile.objects.create(
        conversation=conversation,
        uploaded_by=user,
        file=uploaded_file,
        file_type=file_type,
        original_name=uploaded_file.name,
    )

    return JsonResponse({
        'success': True,
        'file_id': shared_file.id,
        'file_type': file_type,
        'file_url': shared_file.file.url,
        'original_name': shared_file.original_name,
        'uploaded_by': user.get_full_name() or user.username,
    })