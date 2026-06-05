from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_home, name="ai_tutor_home"),
    path("new/", views.new_chat, name="ai_tutor_new"),

    path("chat/<int:chat_id>/", views.chat_page, name="ai_tutor_chat"),

    path("chat/<int:chat_id>/rename/", views.rename_chat, name="ai_tutor_rename"),
    path("chat/<int:chat_id>/delete/", views.delete_chat, name="ai_tutor_delete"),
    path("chat/<int:chat_id>/archive/", views.archive_chat, name="ai_tutor_archive"),
    path("chat/<int:chat_id>/unarchive/", views.unarchive_chat, name="ai_tutor_unarchive"),
    path("chat/<int:chat_id>/share/", views.share_chat, name="ai_tutor_share"),

    path("share/<uuid:token>/", views.shared_chat_view, name="ai_tutor_shared_view"),

    path("msg/<int:msg_id>/regenerate/", views.regenerate_answer, name="ai_tutor_regenerate"),
    path("msg/<int:msg_id>/shorter/", views.make_shorter, name="ai_tutor_shorter"),
    path("msg/<int:msg_id>/easier/", views.make_easier, name="ai_tutor_easier"),
    path("msg/<int:msg_id>/save/", views.save_answer, name="ai_tutor_save"),
    path("msg/<int:msg_id>/quiz/", views.generate_quiz, name="ai_tutor_quiz"),

    path("chat/<int:chat_id>/upload/", views.upload_file, name="ai_tutor_upload"),
]