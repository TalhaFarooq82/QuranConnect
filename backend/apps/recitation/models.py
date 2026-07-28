from django.db import models
from apps.users.models import CustomUser
# Create your models here.
"""
    Stores a user's Quran recitation attempt and feedback.
    """
# Model to store each user's Quran recitation attempt and feedback

class RecitationAttempt(models.Model):
    user = models.ForeignKey(CustomUser, on_delete= models.CASCADE)   # User who submitted the recitation
    score = models.IntegerField(default=0)  # Score assigned after evaluating the recitation
    ayah_number = models.IntegerField() # Ayah number that was recited
    surah_number = models.IntegerField()

    audio_file = models.FileField(upload_to='recitation/')
    user_text = models.TextField()
    correct_text = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'recitation_feedback_table'
        ordering = ['created_at']
        verbose_name = "Recitation Attempt"
        verbose_name_plural = "Recitation Attempts"
