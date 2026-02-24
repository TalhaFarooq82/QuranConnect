from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, TutorProfile    

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
    

class ProfileImageForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_image']
        
class TutorCertificationForm(forms.ModelForm):
    class Meta:
        model = TutorProfile
        fields = [
            'higher_qualification',
            'institute_name',
            'teaching_experience',
            'certification'
        ]   
    
