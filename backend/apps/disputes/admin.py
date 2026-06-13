from django.contrib import admin
from django.contrib import messages
from apps.payments.models import Wallet
from apps.notifications.models import Notification
from .models import Dispute, DisputeMessage


class DisputeMessageInline(admin.TabularInline):
    model = DisputeMessage
    extra = 1


class DisputeAdmin(admin.ModelAdmin):
    list_display = ['id', 'filed_user', 'reported_user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['filed_user__username', 'reported_user__username']
    inlines = [DisputeMessageInline]
    readonly_fields = ['filed_user', 'reported_user', 'job', 'reason',
                       'description', 'evidence_file', 'created_at', 'updated_at']

    actions = ['mark_under_review', 'mark_resolved', 'mark_rejected',
               'warn_reported_user', 'ban_reported_user', 'refund_filed_user']

    def mark_under_review(self, request, queryset):
        queryset.update(status='under_review')
        for dispute in queryset:
            Notification.objects.create(
                user=dispute.filed_user,
                type='dispute',
                title='Dispute Under Review',
                body=f'Your dispute #{dispute.id} is now under review by the admin.',
            )
            Notification.objects.create(
                user=dispute.reported_user,
                type='dispute',
                title='Dispute Under Review',
                body=f'A dispute filed against you (#{dispute.id}) is now under review.',
            )
        self.message_user(request, "Selected disputes marked as Under Review.")
    mark_under_review.short_description = "Mark as Under Review"

    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved')
        for dispute in queryset:
            Notification.objects.create(
                user=dispute.filed_user,
                type='dispute',
                title='Dispute Resolved',
                body=f'Your dispute #{dispute.id} has been resolved by the admin.',
            )
            Notification.objects.create(
                user=dispute.reported_user,
                type='dispute',
                title='Dispute Resolved',
                body=f'A dispute against you (#{dispute.id}) has been resolved.',
            )
        self.message_user(request, "Selected disputes marked as Resolved.")
    mark_resolved.short_description = "Mark as Resolved"

    def mark_rejected(self, request, queryset):
        queryset.update(status='rejected')
        for dispute in queryset:
            Notification.objects.create(
                user=dispute.filed_user,
                type='dispute',
                title='Dispute Rejected',
                body=f'Your dispute #{dispute.id} has been rejected by the admin.',
            )
            Notification.objects.create(
                user=dispute.reported_user,
                type='dispute',
                title='Dispute Rejected',
                body=f'A dispute against you (#{dispute.id}) has been rejected.',
            )
        self.message_user(request, "Selected disputes marked as Rejected.")
    mark_rejected.short_description = "Mark as Rejected"

    def warn_reported_user(self, request, queryset):
        for dispute in queryset:
            user = dispute.reported_user
            user.is_warned = True
            user.save()
            Notification.objects.create(
                user=user,
                type='dispute',
                title='Warning Issued',
                body=f'You have received a warning from admin regarding dispute #{dispute.id}. Please follow the platform guidelines.',
            )
            Notification.objects.create(
                user=dispute.filed_user,
                type='dispute',
                title='Action Taken',
                body=f'Admin has issued a warning to the reported user in dispute #{dispute.id}.',
            )
        self.message_user(request, "Reported user(s) have been warned.")
    warn_reported_user.short_description = "Warn reported user"

    def ban_reported_user(self, request, queryset):
        for dispute in queryset:
            user = dispute.reported_user
            user.is_banned = True
            user.is_active = False
            user.save()
            Notification.objects.create(
                user=dispute.filed_user,
                type='dispute',
                title='User Banned',
                body=f'Admin has banned the reported user in dispute #{dispute.id}.',
            )
        self.message_user(request, "Reported user(s) have been banned.")
    ban_reported_user.short_description = "Ban reported user"

    def refund_filed_user(self, request, queryset):
        for dispute in queryset:
            wallet, _ = Wallet.objects.get_or_create(user=dispute.filed_user)
            wallet.balance += 100
            wallet.save()
            Notification.objects.create(
                user=dispute.filed_user,
                type='dispute',
                title='Refund Issued',
                body=f'A refund of $100 has been added to your wallet for dispute #{dispute.id}.',
            )
        self.message_user(request, "Refund of $100 issued to filed user(s).")
    refund_filed_user.short_description = "Refund $100 to filed user"


admin.site.register(Dispute, DisputeAdmin)
admin.site.register(DisputeMessage)