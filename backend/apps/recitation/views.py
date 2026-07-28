from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.recitation.services import analyze_recitation, save_recitation
from django.http import JsonResponse
from apps.recitation.models import RecitationAttempt
import tempfile, os

# Create your views here.

@login_required
def recitation_page(request):
    if request.method == 'GET':
        
        # Fetch user's previous recitation attempts
        history = RecitationAttempt.objects.filter(
            user=request.user).order_by('-created_at')[:10]  # last 10 attempts

        return render(request, 'recitation/recitation_page.html', {
            'history': history
        })
    
    if request.method == 'POST':
        #Step 1: Get audio file from request 
        audio_file = request.FILES['audio_file']
        
        # Step 2: Save file temporarily to disk
        
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.mp3'
        ) as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_path = temp_file.name

        #Step 3: Anlayze results
        result = analyze_recitation(temp_path)

        #Step 4: Save to database
        save_recitation(request.user, audio_file, result)

        #Step 5: remove temp path
        os.unlink(temp_path)

        #Step 6: Return the answer
        return JsonResponse({
            'surah':     result['surah'],
            'ayah':      result['ayah'],
            'score':     result['score'],
            'feedback':  result['feedback'],
            'user_text': result['user_text']
        })


        
