from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'gender']

    def save(self, commit=True):
        user = super().save(commit=False)
        # role is already selected in the form
        if commit:
            user.save()
        return user
    class Meta:
        db_table = 'users_table'

class TutorCertificationForm(forms.Form):
    certification = forms.FileField(required=True)
    class Meta:
        db_table = 'tutor_certifications'
