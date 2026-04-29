from django.urls import path
from .views import chat_page, new_chat, delete_session

urlpatterns = [
    path('chat/',                    chat_page,      name='chat_page'),
    path('chat/<int:session_id>/',   chat_page,      name='chat_session'),
    path('chat/new/',                new_chat,       name='new_chat'),
    path('chat/delete/<int:session_id>/', delete_session, name='delete_session'),
]