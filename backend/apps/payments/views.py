from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from apps.bookings.models import Job
from apps.notifications.models import Notification
from .models import Wallet, EscrowRecord, WalletTransaction
import stripe

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def release_escrow(request, job_id):
    print("=== release_escrow view called ===")
    print("Method:", request.method)
    print("Job ID:", job_id)

    job = get_object_or_404(Job, id=job_id)

    if job.student != request.user:
        return redirect("student_dashboard")

    from django.db.models import Q

    escrow = get_object_or_404(
        EscrowRecord.objects.filter(
            Q(current_state="held") | Q(current_state="frozen")
        ),
        job=job
    )

    if request.method == "POST":
        print("POST received, releasing escrow...")
        tutor_wallet, _ = Wallet.objects.get_or_create(user=escrow.tutor)
        tutor_wallet.balance += escrow.locked_amount
        tutor_wallet.save()

        WalletTransaction.objects.create(
            wallet=tutor_wallet,
            transaction_type='credit',
            amount=escrow.locked_amount,
            note=f"Payment released for job: {job.title}",
        )

        student_wallet, _ = Wallet.objects.get_or_create(user=request.user)
        WalletTransaction.objects.create(
            wallet=student_wallet,
            transaction_type='debit',
            amount=escrow.locked_amount,
            note=f"Payment sent for job: {job.title}",
        )

        
        escrow.current_state = 'released'
        escrow.save()

        job.status = 'Closed'
        job.save()

        Notification.objects.create(
            user=escrow.tutor,
            type='award',
            title='Payment Released',
            body=f"${escrow.locked_amount} has been released to your wallet for job '{job.title}'.",
        )

        Notification.objects.create(
            user=request.user,
            type='award',
            title='Job Completed',
            body=f"You have marked '{job.title}' as complete. Payment of ${escrow.locked_amount} sent to tutor.",
        )

        messages.success(request, f"Job marked as complete! ${escrow.locked_amount} released to tutor.")

    return redirect("student_request_detail", job_id=job.id)

@login_required
def stripe_checkout(request):
    if request.user.role != 'student':
        return redirect('teacher_active_jobs')

    amount = request.GET.get('amount', '')

    try:
        amount_int = int(float(amount))
        if amount_int < 1:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, "Please enter a valid amount.")
        return redirect('student_dashboard')

    # create Stripe checkout session
    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': 'QuranConnect Wallet Top-up',
                    'description': f'Add ${amount_int} to your QuranConnect wallet',
                },
                'unit_amount': amount_int * 100,  # Stripe uses cents
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=request.build_absolute_uri(
            f'/payments/stripe/success/?amount={amount_int}'
        ),
        cancel_url=request.build_absolute_uri('/payments/stripe/cancel/'),
        metadata={
            'user_id': request.user.id,
            'amount': amount_int,
        }
    )

    return redirect(checkout_session.url)

@login_required
def stripe_success(request):
    amount = request.GET.get('amount', 0)

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        amount = 0

    if amount > 0:
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        wallet.balance += amount
        wallet.save()

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type='credit',
            amount=amount,
            note=f"Stripe payment: ${amount} added to wallet",
        )

        Notification.objects.create(
            user=request.user,
            type='award',
            title='Funds Added ✅',
            body=f"${amount} has been added to your wallet via Stripe.",
        )

        messages.success(request, f"${amount} successfully added to your wallet!")

    return redirect('student_dashboard')


@login_required
def stripe_cancel(request):
    messages.error(request, "Payment cancelled. No charges were made.")
    return redirect('student_dashboard')
