from django.db import models
from apps.users.models import CustomUser
from apps.bookings.models import Job
# Create your models here.
class Dispute(models.Model):
    STATUS_CHOICES = [
    ('open', 'Open'),
    ('under_review', 'Under Review'),
    ('resolved', 'Resolved'),
    ('rejected', 'Rejected'),
    ]

    filed_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='disputes_filed')
    reported_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='disputes_received')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True)
    reason = models.TextField()
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    evidence_file = models.FileField(upload_to='dispute_files', null=True, blank=True)
    resolution_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dispute #{self.id} by {self.filed_user} — {self.status}"
    class Meta:
        db_table = 'dispute_table'


class DisputeMessage(models.Model):
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='dispute_messages')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.sender} on Dispute #{self.dispute.id}"

    class Meta:
        db_table = 'dispute_messages'
    