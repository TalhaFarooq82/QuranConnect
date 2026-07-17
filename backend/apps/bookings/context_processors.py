from apps.payments.models import Wallet
from apps.notifications.models import Notification


def wallet_context(request):
    if request.user.is_authenticated:
        wallet, _ = Wallet.objects.get_or_create(user=request.user)
        
        unread_notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()

        unread_messages = Notification.objects.filter(
            user=request.user,
            type='message',
            is_read=False
        ).count()

        return {
            'wallet': wallet,
            'unread_notifications': unread_notifications,
            'unread_messages': unread_messages,
        }
    return {
        'wallet': None,
        'unread_notifications': 0,
        'unread_messages': 0,
    }