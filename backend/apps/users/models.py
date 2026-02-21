from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('tutor', 'Tutor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True, blank=True)

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)

class TutorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    certification = models.FileField(upload_to='certifications/')
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username