from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Notification
from apps.payments.models import Wallet


@login_required
def notifications_page(request):
    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    notifications.update(is_read=True)

    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    return render(request, 'notifications/notifications.html', {
        'notifications': notifications,
        'wallet': wallet,
    })