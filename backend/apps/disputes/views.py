from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.bookings.models import Job
from apps.users.models import CustomUser
from .models import Dispute
from .forms import DisputeForm


@login_required
def dispute_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # figure out who is being reported
    # if student is filing, reported user is the awarded tutor
    # if tutor is filing, reported user is the student who posted the job
    if request.user == job.student:
        reported_user = job.awarded_teacher
    else:
        reported_user = job.student

        # guard against unawarderd job
    if reported_user is None:
        messages.error(request, "Cannot file a dispute — no tutor has been awarded this job yet.")
        return redirect('job_detail', job_id=job_id)
    
    if request.method == 'POST':
        form = DisputeForm(request.POST, request.FILES)
        if form.is_valid():
            dispute = form.save(commit=False)  # don't save to DB yet
            dispute.filed_user = request.user
            dispute.reported_user = reported_user
            dispute.job = job
            dispute.status = 'open'
            dispute.save()
            messages.success(request, "Your dispute has been filed successfully.")
            # redirect based on role
            if request.user.role == 'student':
                return redirect('student_dashboard')
            else:
                return redirect('teacher_active_jobs')

    else:
        form = DisputeForm()

    return render(request, 'disputes/file_dispute.html', {
        'form': form,
        'job': job,
        'reported_user': reported_user,
    })


@login_required
def dispute_user(request, user_id):
    reported_user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        form = DisputeForm(request.POST, request.FILES)
        if form.is_valid():
            dispute = form.save(commit=False)
            dispute.filed_user = request.user
            dispute.reported_user = reported_user
            dispute.status = 'open'
            dispute.save()
            messages.success(request, "Your dispute has been filed successfully.")
            # redirect based on role
            if request.user.role == 'student':
                return redirect('student_dashboard')
            else:
                return redirect('teacher_active_jobs')

    else:
        form = DisputeForm()

    return render(request, 'disputes/file_dispute.html', {
        'form': form,
        'reported_user': reported_user,
    })