from django.db import models
from django.conf import settings
from apps.bookings.models import Conversation


class SharedFile(models.Model):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('pdf', 'PDF'),
        ('doc', 'Document'),
        ('audio', 'Audio'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='shared_files'
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='uploaded_files'
    )
    file = models.FileField(upload_to='chat_files/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES)
    original_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.original_name} in conversation {self.conversation.id}"