from django.urls import path
from . import views

urlpatterns = [
    path('tutor/<int:tutor_id>/review/', views.submit_review, name='submit_review')
]


