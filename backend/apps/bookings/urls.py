from django.urls import path
from . import views

urlpatterns = [
    path("teacher/active-jobs/", views.teacher_active_jobs, name="teacher_active_jobs"),
    path("teacher/job/<int:job_id>/", views.job_detail, name="job_detail"),

    path("student/post-job/", views.post_job, name="post_job"),
    path("student/post-job/logistics/", views.post_job_logistics, name="post_job_logistics"),
    path("student/post-job/success/", views.post_job_success, name="post_job_success"),

    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/request/<int:job_id>/", views.student_request_detail, name="student_request_detail"),
    path("proposal/<int:proposal_id>/award/", views.award_project, name="award_project"),

    path("chat/<int:job_id>/", views.chat_room, name="chat_room"),
    path("wallet/add-funds/", views.add_funds, name="add_funds"),
]