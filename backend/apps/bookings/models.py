from django.conf import settings
from django.db import models

class Wallet(models.Model):
    user = models.OneToOneField 
    (
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallet"
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} - {self.balance}"

class Job(models.Model):
    STATUS_CHOICES = [
        ("Open", "Open"),
        ("Awarded", "Awarded"),
        ("Closed", "Closed"),
    ]

    student = models.ForeignKey 
(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posted_jobs",
        null=True,
        blank=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.CharField(max_length=50)
    course = models.CharField(max_length=100)
    schedule = models.CharField(max_length=150)
    duration = models.CharField(max_length=100)
    preferred_gender = models.CharField(max_length=50)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Open")
    awarded_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="awarded_jobs",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Proposal(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Awarded", "Awarded"),
        ("Rejected", "Rejected"),
    ]

    job = models.ForeignKey
(
        Job,
        on_delete=models.CASCADE,
        related_name="proposals"
    )
    teacher = models.ForeignKey
(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    related_name="submitted_proposals",
    null=True,
    blank=True
)
    hourly_rate = models.CharField(max_length=50)
    proposal_text = models.TextField()
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.9)
    reviews = models.IntegerField(default=0)
    availability = models.CharField(max_length=100, default="Available Immediately")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "teacher")

    def __str__(self):
        return f"{self.teacher.username} - {self.job.title}"


class Conversation(models.Model):
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_conversations"
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teacher_conversations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("job", "teacher")

    def __str__(self):
        return f"{self.job.title} - {self.teacher.username}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message by {self.sender.username}"


class Notification(models.Model):
    TYPE_CHOICES = [
        ("proposal", "proposal"),
        ("award", "award"),
        ("message", "message"),
    ]

    user = models.ForeignKey
(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"
