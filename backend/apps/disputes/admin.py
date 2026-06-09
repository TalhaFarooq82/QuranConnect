from django.contrib import admin
from apps.disputes.models import Dispute, DisputeMessage
# Register your models here.
admin.site.register(Dispute)
admin.site.register(DisputeMessage)