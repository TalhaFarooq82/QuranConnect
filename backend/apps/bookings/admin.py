from django.contrib import admin
from .models import Job, Proposal, Conversation, Message, Notification

admin.site.register(Job)
admin.site.register(Proposal)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Notification)