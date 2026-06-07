from django.contrib import admin
from .models import CustomUser, StudentProfile, TutorProfile

admin.site.register(CustomUser)
admin.site.register(StudentProfile)
admin.site.register(TutorProfile)