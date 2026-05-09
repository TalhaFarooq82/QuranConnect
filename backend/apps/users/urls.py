from django.urls import path
from .views import (
    register_choice,
    user_signup,
    tutor_certification,
    upload_profile,
    login_view,
    logout_view
)

urlpatterns = [
    #→ Role selection
    path('register/', register_choice, name='register_choice'),

    #→ Signup based on role
    path('signup/<str:role>/', user_signup, name='user_signup'),

    #upload pic
    path('upload-profile/', upload_profile, name='upload_profile'),

    #→ Tutor Certification upload
    path('register/tutor/certification/<int:user_id>/', tutor_certification, name='tutor_certification'),
    
    # login
    path('login/', login_view, name = 'login'),

    #logout
    path('logout/', logout_view, name='logout')
]