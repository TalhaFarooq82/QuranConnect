from django.urls import path
from . import views

urlpatterns = [
    path('notifications/', views.notifications_page, name='notifications'),
]