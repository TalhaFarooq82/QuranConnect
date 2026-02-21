from django.urls import path
from .views import (
    register_choice,
    student_signup,
    tutor_signup,
    tutor_certification
)

urlpatterns = [
    # Step 0 → Role selection
    path('register/', register_choice, name='register_choice'),

    # Step 1 → Signup based on role
    path('register/student/', student_signup, name='student_signup'),
    path('register/tutor/', tutor_signup, name='tutor_signup'),

    # Step 2 → Tutor Certification upload
    path('register/tutor/certification/<int:user_id>/', tutor_certification, name='tutor_certification'),
]