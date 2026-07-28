from django.db import models
from django.conf import settings
from apps.bookings.models import Job


class Wallet(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - {self.balance}"

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("credit", "Credit"),
        ("debit", "Debit"),
    ]

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.wallet.user.username} - {self.transaction_type} - {self.amount}"

class EscrowRecord(models.Model):
    STATE_CHOICES = [
        ('held', 'Held'),
        ('released', 'Released'),
        ('refunded', 'Refunded'),
        ('frozen', 'Frozen'),
        ]
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='escrow_as_student')
    tutor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='escrow_as_tutor')
    locked_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_state = models.CharField(max_length=20, choices=STATE_CHOICES,default='held')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Escrow #{self.id} - {self.job.title} - {self.current_state}"
    
    class Meta:
        db_table = 'escrow_records'
