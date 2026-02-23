from django.urls import path
from .views import (
    register_choice,
    user_signup,
    tutor_certification,
    upload_profile,
)

urlpatterns = [
    # Step 0 → Role selection
    path('register/', register_choice, name='register_choice'),

    # Step 1 → Signup based on role
    path('signup/<str:role>/', user_signup, name='user_signup'),

    # Step 2 → Tutor Certification upload
    path('register/tutor/certification/<int:user_id>/', tutor_certification, name='tutor_certification'),
    path('upload-profile/', upload_profile, name='upload_profile'),
]