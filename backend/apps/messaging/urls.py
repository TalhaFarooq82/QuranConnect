from django.urls import path
from . import views

urlpatterns = [
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:conversation_id>/', views.chat_room, name='messaging_chat_room'),
    path('inbox/<int:conversation_id>/upload/', views.upload_file, name='upload_file'),
]