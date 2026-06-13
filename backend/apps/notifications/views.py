from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notifications_page(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # mark all as read when user visits the page
    notifications.update(is_read=True)

    return render(request, 'notifications/notifications.html', {
        'notifications': notifications,
    })