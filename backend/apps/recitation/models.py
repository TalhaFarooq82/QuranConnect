from django.db import models
from apps.users.models import CustomUser
# Create your models here.

class RecitationAttempt(models.Model):
    user = models.ForeignKey(CustomUser, on_delete= models.CASCADE)
    score = models.IntegerField(default=0)
    ayah_number = models.IntegerField()
    surah_number = models.IntegerField()

    audio_file = models.FileField(upload_to='recitation/')
    user_text = models.TextField()
    correct_text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recitation_feedback_table'
        ordering = ['created_at']
