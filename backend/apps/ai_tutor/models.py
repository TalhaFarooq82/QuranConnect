from django.db import models
from apps.users.models import CustomUser
from django.conf import settings
import uuid

# Create your models here.
class ChatSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200, blank=True, default="")
    class Meta:
        db_table = 'chat_sessions'

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'chat_messages'
        ordering = ['created_at']

class TutorChat(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tutor_chats")
    title = models.CharField(max_length=120, default="New Chat")
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class TutorMessage(models.Model):
    ROLE_CHOICES = [("user", "User"), ("assistant", "Assistant")]

    chat = models.ForeignKey(TutorChat, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    saved = models.BooleanField(default=False)  # "Save answer"
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.chat_id} - {self.role}"


class TutorShareLink(models.Model):
    chat = models.ForeignKey(TutorChat, on_delete=models.CASCADE, related_name="share_links")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class TutorUpload(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tutor_uploads")
    chat = models.ForeignKey(TutorChat, on_delete=models.CASCADE, related_name="uploads")
    file = models.FileField(upload_to="ai_tutor_uploads/")
    filename = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)  # store parsed text here
    created_at = models.DateTimeField(auto_now_add=True)