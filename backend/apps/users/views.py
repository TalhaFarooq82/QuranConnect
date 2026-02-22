from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from .forms import CustomUserCreationForm, TutorCertificationForm
from .models import CustomUser, TutorProfile

def home(request):
    return render(request, 'home.html')

# Step 0 → Role selection page
def register_choice(request):
    return render(request, 'users/register_choice.html')


# Step 1 → Student signup
def student_signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'student'  # force role
            user.save()
            login(request, user)
            return redirect('dashboard')
        else:
            print(form.errors)  # debug
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/student_signup.html', {'form': form})


# Step 1 → Tutor signup (basic info)
def tutor_signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        # #  ADD THESE TWO LINES HERE
        # print("FORM VALID:", form.is_valid())
        # print("FORM ERRORS:", form.errors)

        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'tutor'  # force role
            user.save()
            return redirect('tutor_certification', user_id=user.id)
        else:
            print(form.errors)  # debug
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/tutor_signup.html', {'form': form})


# Step 2 → Tutor certification upload
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