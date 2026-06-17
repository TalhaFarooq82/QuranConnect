from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.bookings.models import Job
from apps.notifications.models import Notification
from .models import Wallet, EscrowRecord, WalletTransaction


@login_required
def release_escrow(request, job_id):
    job = get_object_or_404(Job, id=job_id)

    # only the student who posted the job can mark it complete
    if job.student != request.user:
        return redirect("student_dashboard")

    # get the held escrow record for this job
    escrow = get_object_or_404(EscrowRecord, job=job, current_state='held')

    if request.method == "POST":

        # Step 1 — add funds to tutor wallet
        tutor_wallet, _ = Wallet.objects.get_or_create(user=escrow.tutor)
        tutor_wallet.balance += escrow.locked_amount
        tutor_wallet.save()

        # Step 2 — log transaction for tutor
        WalletTransaction.objects.create(
            wallet=tutor_wallet,
            transaction_type='credit',
            amount=escrow.locked_amount,
            note=f"Payment released for job: {job.title}",
        )

        # Step 3 — log transaction for student
        student_wallet, _ = Wallet.objects.get_or_create(user=request.user)
        WalletTransaction.objects.create(
            wallet=student_wallet,
            transaction_type='debit',
            amount=escrow.locked_amount,
            note=f"Payment sent for job: {job.title}",
        )

        # Step 4 — update escrow state
        escrow.current_state = 'released'
        escrow.save()

        # Step 5 — close the job
        job.status = 'Closed'
        job.save()

        # Step 6 — notify tutor
        Notification.objects.create(
            user=escrow.tutor,
            type='award',
            title='Payment Released',
            body=f"${escrow.locked_amount} has been released to your wallet for job '{job.title}'.",
        )

        # Step 7 — notify student
        Notification.objects.create(
            user=request.user,
            type='award',
            title='Job Completed',
            body=f"You have marked '{job.title}' as complete. Payment of ${escrow.locked_amount} sent to tutor.",
        )

        messages.success(request, f"Job marked as complete! ${escrow.locked_amount} released to tutor.")

    return redirect("student_request_detail", job_id=job.id)