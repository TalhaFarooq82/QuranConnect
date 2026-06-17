from django.urls import path
from . import views

urlpatterns = [
    path('job/<int:job_id>/release-escrow/', views.release_escrow, name='release_escrow')
]
