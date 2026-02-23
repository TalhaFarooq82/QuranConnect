from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import CustomUserCreationForm, TutorCertificationForm, ProfileImageForm
from .models import CustomUser, TutorProfile

def home(request):
    return render(request, 'home.html')

# → Role selection page
def register_choice(request):
    return render(request, 'users/register_choice.html')

#first signup page of both student and tutor
def user_signup(request, role):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = role  # assign role dynamically
            user.save()
            login(request, user)
            return redirect('upload_profile')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/user_signup.html', {'form': form, 'role': role})


# upload the profile pic
from django.contrib.auth.decorators import login_required

@login_required
def upload_profile(request):

    if request.method == 'POST':
        form = ProfileImageForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            form.save()

            # If student → go to dashboard
            if request.user.role == 'student':
                return redirect('dashboard')

            # If tutor → go to certification step
            elif request.user.role == 'tutor':
                return redirect('tutor_certification', user_id=request.user.id)

    else:
        form = ProfileImageForm(instance=request.user)

    return render(request, 'users/upload_profilepic.html', {'form': form})

# → Tutor certification upload
def tutor_certification(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        form = TutorCertificationForm(request.POST, request.FILES)
        if form.is_valid():
            TutorProfile.objects.create(
                user=user,
                certification=form.cleaned_data['certification']
            )
            login(request, user)
            return redirect('dashboard')
    else:
        form = TutorCertificationForm()

    return render(request, 'users/tutor_certification.html', {'form': form})