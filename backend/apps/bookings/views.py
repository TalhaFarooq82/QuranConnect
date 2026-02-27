from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Job, Proposal, Wallet, Notification, Conversation, Message


@login_required
def teacher_active_jobs(request):
    jobs = Job.objects.filter(status="Open").order_by("-created_at")
    return render(request, "bookings/teacher_active_jobs.html", {
        "jobs": jobs,
        "total_results": jobs.count(),
    })


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.method == "POST":
        rate = request.POST.get("rate", "").strip()
        proposal_text = request.POST.get("proposal", "").strip()

        if rate and proposal_text:
            proposal, created = Proposal.objects.get_or_create(
                job=job,
                teacher=request.user,
                defaults={
                    "hourly_rate": rate,
                    "proposal_text": proposal_text,
                    "rating": 4.9,
                    "reviews": 23,
                    "availability": "Available Immediately",
                },
            )

            if not created:
                proposal.hourly_rate = rate
                proposal.proposal_text = proposal_text
                proposal.save()

            Notification.objects.create(
                user=job.student,
                type="proposal",
                title="New proposal received",
                body=f"{request.user.username} submitted a proposal on '{job.title}'.",
            )

            return redirect("job_detail", job_id=job.id)

    proposals = job.proposals.all().order_by("-created_at")

    return render(request, "bookings/job_detail.html", {
        "job": job,
        "proposals": proposals,
        "can_bid": request.user != job.student and job.status == "Open",
    })


@login_required
def post_job(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        course = request.POST.get("course", "").strip()
        description = request.POST.get("description", "").strip()
        preferred_gender = request.POST.get("preferred_gender", "").strip()

        if title and course and description and preferred_gender:
            request.session["post_job_step1"] = {
                "title": title,
                "course": course,
                "description": description,
                "preferred_gender": preferred_gender,
            }
            return redirect("post_job_logistics")

        return render(request, "bookings/post_job.html", {"error": "Please fill in all fields."})

    return render(request, "bookings/post_job.html")


@login_required
def post_job_logistics(request):
    step1_data = request.session.get("post_job_step1")
    if not step1_data:
        return redirect("post_job")

    if request.method == "POST":
        start_time = request.POST.get("start_time", "").strip()
        end_time = request.POST.get("end_time", "").strip()
        budget_type = request.POST.get("budget_type", "").strip()
        budget_min = request.POST.get("budget_min", "").strip()
        budget_max = request.POST.get("budget_max", "").strip()

        if start_time and end_time and budget_type and budget_min and budget_max:
            budget = f"${budget_min} - ${budget_max} / hr" if budget_type == "hourly" else f"${budget_min} - ${budget_max} fixed"
            schedule = f"{start_time} - {end_time} (PKT)"

            job = Job.objects.create(
                student=request.user,
                title=step1_data["title"],
                description=step1_data["description"],
                budget=budget,
                course=step1_data["course"],
                schedule=schedule,
                duration="To be discussed",
                preferred_gender=step1_data["preferred_gender"],
                status="Open",
            )

            request.session.pop("post_job_step1", None)
            request.session["last_posted_job_id"] = job.id
            return redirect("post_job_success")

        return render(request, "bookings/post_job_logistics.html", {"error": "Please fill in all fields."})

    return render(request, "bookings/post_job_logistics.html")


@login_required
def post_job_success(request):
    job_id = request.session.get("last_posted_job_id")
    if not job_id:
        return redirect("post_job")

    job = get_object_or_404(Job, id=job_id, student=request.user)
    return render(request, "bookings/post_job_success.html", {"job": job})


@login_required
def student_dashboard(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    jobs = Job.objects.filter(student=request.user).order_by("-created_at")
    notifications = request.user.notifications.order_by("-created_at")[:5]

    total_requests = jobs.count()
    open_requests = jobs.filter(status="Open").count()
    assigned_requests = jobs.filter(status="Awarded").count()
    total_proposals = Proposal.objects.filter(job__student=request.user).count()

    return render(request, "bookings/student_dashboard.html", {
        "student": request.user,
        "wallet": wallet,
        "notifications": notifications,
        "total_requests": total_requests,
        "open_requests": open_requests,
        "assigned_requests": assigned_requests,
        "total_proposals": total_proposals,
        "recent_jobs": jobs[:5],
        "unread_messages": Notification.objects.filter(user=request.user, type="message", is_read=False).count(),
    })


@login_required
def add_funds(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        amount = request.POST.get("amount", "").strip()
        if amount:
            wallet.balance += Decimal(amount)
            wallet.save()

    return redirect("student_dashboard")


@login_required
def award_project(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id)
    job = proposal.job

    if job.student != request.user:
        return redirect("student_dashboard")

    if request.method == "POST" and job.status == "Open":
        proposal.status = "Awarded"
        proposal.save()

        Proposal.objects.filter(job=job).exclude(id=proposal.id).update(status="Rejected")
        job.status = "Awarded"
        job.awarded_teacher = proposal.teacher
        job.save()

        Conversation.objects.get_or_create(
            job=job,
            defaults={
                "student": job.student,
                "teacher": proposal.teacher,
            }
        )

        Notification.objects.create(
            user=proposal.teacher,
            type="award",
            title="Project awarded",
            body=f"You have been awarded the project '{job.title}'.",
        )

    return redirect("student_request_detail", job.id)


@login_required
def student_request_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, student=request.user)
    proposals = job.proposals.select_related("teacher").order_by("-created_at")

    return render(request, "bookings/student_request_detail.html", {
        "job": job,
        "proposals": proposals,
    })


@login_required
def chat_room(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    conversation = get_object_or_404(Conversation, job=job)

    if request.user != conversation.student and request.user != conversation.teacher:
        return redirect("student_dashboard")

    if request.method == "POST":
        body = request.POST.get("body", "").strip()
        if body:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                body=body,
            )

            recipient = conversation.teacher if request.user == conversation.student else conversation.student

            Notification.objects.create(
                user=recipient,
                type="message",
                title="New message",
                body=f"You received a new message in '{job.title}'.",
            )

            return redirect("chat_room", job_id=job.id)

    messages = conversation.messages.select_related("sender").order_by("created_at")

    return render(request, "bookings/chat_room.html", {
        "job": job,
        "conversation": conversation,
        "messages": messages,
    })