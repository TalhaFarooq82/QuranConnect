from decimal import Decimal, InvalidOperation
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Job, Proposal, Conversation, Message
from apps.notifications.models import Notification
from apps.payments.models import Wallet
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from apps.recommendations.services import get_ranked_proposals


@login_required
def teacher_active_jobs(request):
    jobs = Job.objects.filter(status="Open").order_by("-created_at")
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    notifications = request.user.notifications.order_by("-created_at")[:5]

    unread_messages = Notification.objects.filter(
        user=request.user,
        type="message",
        is_read=False
    ).count()

    return render(request, "bookings/teacher_active_jobs.html", {
        "jobs": jobs,
        "total_results": jobs.count(),
        "unread_messages": unread_messages,
        "wallet": wallet,
        "notifications": notifications,

    })

@login_required
def teacher_profile(request):
    if request.user.role != "tutor":
        return redirect("student_dashboard")

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    return render(request, "bookings/teacher_profile.html", {
        "wallet": wallet,
    })


@login_required
def withdraw_funds(request):
    if request.user.role != "tutor":
        return redirect("student_dashboard")

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    if request.method == "POST":
        raw_amount = request.POST.get("amount", "").strip()

        try:
            amount = Decimal(raw_amount)
        except (InvalidOperation, TypeError):
            messages.error(request, "Please enter a valid amount.")
            return redirect("teacher_profile")

        if amount <= 0:
            messages.error(request, "Withdrawal amount must be greater than zero.")
            return redirect("teacher_profile")

        if amount > wallet.balance:
            messages.error(request, "You do not have enough balance to withdraw that amount.")
            return redirect("teacher_profile")

        wallet.balance -= amount
        wallet.save()

        messages.success(request, f"${amount} has been withdrawn successfully.")
        return redirect("teacher_profile")

    return redirect("teacher_profile")


@login_required
def teacher_settings(request):
    if request.user.role != "tutor":
        return redirect("student_dashboard")

    if request.method == "POST":
        request.user.first_name = request.POST.get("first_name", "").strip()
        request.user.last_name = request.POST.get("last_name", "").strip()
        request.user.email = request.POST.get("email", "").strip()

        if "profile_image" in request.FILES:
            request.user.profile_image = request.FILES["profile_image"]

        request.user.save()
        messages.success(request, "Your settings have been updated.")
        return redirect("teacher_settings")

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    return render(request, "bookings/teacher_settings.html", {
        "wallet": wallet,
    })


@login_required
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    if request.user.role != "tutor":
        return redirect("student_dashboard")

    existing_proposal = Proposal.objects.filter(job=job, teacher=request.user).first()

    if request.method == "POST" and job.status == "Open" and not existing_proposal:
        hourly_rate = request.POST.get("rate", "").strip()
        proposal_text = request.POST.get("proposal", "").strip()

        if hourly_rate and proposal_text:
            Proposal.objects.create(
                job=job,
                teacher=request.user,
                hourly_rate=hourly_rate,
                proposal_text=proposal_text,
                rating=4.9,
                reviews=0,
                availability="Available Immediately",
            )

            Notification.objects.create(
                user=job.student,
                type="proposal",
                title="New proposal received",
                body=f"{request.user.get_full_name() or request.user.username} submitted a proposal for '{job.title}'.",
            )

            return redirect("job_detail", job_id=job.id)

    proposals = job.proposals.select_related("teacher").order_by("-created_at")

    return render(request, "bookings/job_detail.html", {
        "job": job,
        "proposals": proposals,
        "existing_proposal": existing_proposal,
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
            teacher=proposal.teacher,
            defaults={
                "student": job.student,
            }
        )

        Notification.objects.create(
            user=proposal.teacher,
            type="award",
            title="Project awarded",
            body=f"You have been awarded with the project '{job.title}'.",
        )

    return redirect("student_request_detail", job_id=job.id)


@login_required
def student_request_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id, student=request.user)
    ranked = get_ranked_proposals(job)
    return render(request, "bookings/student_request_detail.html", {
        "job":    job,
        "ranked": ranked,
    })

@login_required
def start_chat(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id)
    job = proposal.job

    if job.student != request.user:
        return redirect("student_dashboard")

    conversation, created = Conversation.objects.get_or_create(
        job=job,
        teacher=proposal.teacher,
        defaults={
            "student": request.user,
        }
    )

    if created:
        Notification.objects.create(
            user=proposal.teacher,
            type="message",
            title="New chat started",
            body=f"{request.user.username} started a chat with you for '{job.title}'.",
        )

    return redirect("messaging_chat_room", conversation_id=conversation.id)


@login_required
def chat_room(request, conversation_id):
    conversation = get_object_or_404(
        Conversation.objects.select_related("job", "student", "teacher"),
        id=conversation_id
    )

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
                body=f"You received a new message in '{conversation.job.title}'.",
            )

            return redirect("messaging_chat_room", conversation_id=conversation.id)

    messages = conversation.messages.select_related("sender").order_by("created_at")

    return render(request, "bookings/chat_room.html", {
        "conversation": conversation,
        "job": conversation.job,
        "messages": messages,
    })