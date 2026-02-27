from django.contrib import admin
from .models import Job, Proposal
from .models import Wallet, Job, Proposal, Conversation, Message, Notification

admin.site.register(Job)
admin.site.register(Proposal)
admin.site.register(Wallet)
admin.site.register(Conversation)
admin.site.register(Message)
admin.site.register(Notification)