from django.contrib import admin
from .models import CustomUser, StudentProfile, TutorProfile


class TutorProfileAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if change:  # only on updates not creation
            try:
                old = TutorProfile.objects.get(pk=obj.pk)
                old_status = old.verification_status
            except TutorProfile.DoesNotExist:
                old_status = None

            super().save_model(request, obj, form, change)

            # status changed — notify tutor
            if old_status != obj.verification_status:
                from apps.notifications.models import Notification

                if obj.verification_status == 'approved':
                    obj.is_verified = True
                    obj.save()
                    Notification.objects.create(
                        user=obj.user,
                        type='award',
                        title='Profile Verified ✅',
                        body='Congratulations! Your profile has been verified. You can now bid on jobs.',
                    )
                elif obj.verification_status == 'rejected':
                    obj.is_verified = False
                    obj.save()
                    Notification.objects.create(
                        user=obj.user,
                        type='dispute',
                        title='Verification Rejected ❌',
                        body='Your CNIC verification was rejected. Please upload a clearer image in Settings.',
                    )
                elif obj.verification_status == 'unverified':
                    obj.is_verified = False
                    obj.save()
                    Notification.objects.create(
                        user=obj.user,
                        type='dispute',
                        title='Verification Removed ⚠',
                        body='Your verified status has been removed by admin. Please contact support for more information.',
                    )
                elif obj.verification_status == 'pending':
                    Notification.objects.create(
                        user=obj.user,
                        type='award',
                        title='Verification Under Review ⏳',
                        body='Your CNIC is under review. You will be notified once admin approves your profile.',
                    )
        else:
            super().save_model(request, obj, form, change)


admin.site.register(CustomUser)
admin.site.register(StudentProfile)
admin.site.register(TutorProfile, TutorProfileAdmin)