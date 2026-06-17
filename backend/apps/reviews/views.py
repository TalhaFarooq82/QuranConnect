from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.models import CustomUser
from .models import Review


@login_required
def submit_review(request, tutor_id):
    tutor = get_object_or_404(CustomUser, id=tutor_id)

    # only students can review
    if request.user.role != 'student':
        messages.error(request, "Only students can leave reviews.")
        return redirect('teacher_profile')

    # can't review yourself
    if request.user == tutor:
        messages.error(request, "You cannot review yourself.")
        return redirect('teacher_profile')

    # duplicate check — one review per tutor
    existing = Review.objects.filter(reviewer=request.user, tutor=tutor).first()
    if existing:
        messages.error(request, "You have already reviewed this tutor.")
        return redirect('teacher_profile')

    if request.method == 'POST':
        rating = request.POST.get('rating')

        if not rating:
            messages.error(request, "Please select a rating.")
            return redirect('teacher_profile')

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            messages.error(request, "Invalid rating value.")
            return redirect('teacher_profile')

        Review.objects.create(
            reviewer=request.user,
            tutor=tutor,
            rating=rating,
        )

        messages.success(request, f"Your {rating}★ review has been submitted successfully.")

    return redirect('teacher_profile')