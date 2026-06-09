from django.urls import path
from . import views

urlpatterns = [
    path('file/job/<int:job_id>/', views.dispute_job, name='dispute_job'),
    path('file/user/<int:user_id>/', views.dispute_user, name='dispute_user'),
]