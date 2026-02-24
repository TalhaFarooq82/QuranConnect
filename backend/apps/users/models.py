from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('tutor', 'Tutor'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True)

    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    )
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    class Meta:
        db_table = 'users_table'

class TutorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    higher_qualification = models.CharField(max_length=255, null=True)
    institute_name = models.CharField(max_length=255, null=True)
    teaching_experience = models.PositiveIntegerField(help_text="Experience in years", null=True)

    certification = models.FileField(upload_to='certifications/')
    is_verified = models.BooleanField(default=False)

    class Meta:
        db_table = 'tutor_certifications'

    def __str__(self):
        return self.user.username