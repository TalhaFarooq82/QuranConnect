import os
import difflib
import whisper
import re
import chromadb
from camel_tools.utils.normalize import (
    normalize_unicode,
    normalize_alef_ar,
    normalize_alef_maksura_ar,
    normalize_teh_marbuta_ar
)
from apps.recitation.models import RecitationAttempt

#---------------------------- Whisper Model -----------------------

model = whisper.load_model("base")

CHROMA_DB_PATH = os.path.join(
    os.path.dirname(__file__),   # current folder (recitation/)
    '..', 'ai_tutor', 'chroma_db'   # go up then into ai_tutor/chroma_db
)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_or_create_collection(name="islamic_knowledge")

def clean_whisper_output(text):
    # Step 1: Remove leading numbers
    text = re.sub(r'^\d+[\.\-\)]\s*', '', text.strip())

    # Step 2: Remove tatweel
    text = re.sub(r'\u0640', '', text)

    # Step 3: Convert dagger alef to regular alef BEFORE camel-tools
    text = re.sub(r'\u0670', 'ا', text)

    # Step 4: camel-tools normalization
    text = normalize_unicode(text)
    text = normalize_alef_ar(text)
    text = normalize_alef_maksura_ar(text)
    text = normalize_teh_marbuta_ar(text)

    # Step 5: Remove tashkeel
    tashkeel = re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]')
    text = tashkeel.sub('', text).strip()

    return text

def compare_words(correct_text, user_text):
  correct_words = correct_text.split()
  user_words = user_text.split()

  matcher = difflib.SequenceMatcher(None, correct_words, user_words)
  feedback = []

  for tag, c1, c2, u1, u2 in matcher.get_opcodes():
    if tag == "equal":
      for word in correct_words[c1:c2]:
        feedback.append(
            {
                'word' : word,
                'status' : 'correct'
            }
        )

    elif tag == "replace":
      for k in range(max(c2-c1, u2-u1)):
        correct_word = correct_words[c1+k] if c1+k < c2 else "—"
        user_word    = user_words[u1+k]    if u1+k < u2 else "—"
        feedback.append({
            "word":     correct_word,
            "status":   "wrong",
            "you_said": user_word
        })

    elif tag == "delete":
      for word in correct_words[c1:c2]:
        feedback.append({
             "word":   word,
              "status": "missing"
        })

    elif tag == "insert":
      for word in user_words[u1:u2]:
        feedback.append({
            "word":   word,
            "status": "extra"
        })

  return feedback


def analyze_recitation(audio_file):
    # transcribing the audio.....
    result = model.transcribe(audio_file, language= 'ar')
    # print(f"Voice text: {result['text']}")
    user_text = result['text']
     # text cleaning or preprocessing
    clean_user_text = clean_whisper_output(user_text)

    # get correct aya from chromadb OR Search ChromaDB
    results = collection.query(
        query_texts = [clean_user_text],    # Arabic whisper output
        n_results   = 1,                    # top 1 match only
        where       = {"source": "Quran"},  # ignore hadiths
        include     = ["documents", "metadatas"]
    )

    # Step 4: Extract from metadata
    raw_correct = results['metadatas'][0][0]['arabic_text']
    surah = results['metadatas'][0][0]['surah_number']
    ayah = results['metadatas'][0][0]['ayah_number'] 



    # cleaning the correct text
    clean_correct_text = clean_whisper_output(raw_correct)

    # Now Comparing both text
    feedback = compare_words(clean_correct_text, clean_user_text)

    # Step 7: Calculate score
    total   = len(feedback)
    correct = sum(1 for f in feedback if f["status"] == "correct")
    score   = round((correct / total) * 100) if total > 0 else 0

    # Step 8: Return everything
    return {
        "surah":        surah,
        "ayah":         ayah,
        "correct_text": raw_correct,
        "user_text":    user_text,
        "feedback":     feedback,
        "score":        score
    }

 

def save_recitation(user, audio_file_path, result):
    RecitationAttempt.objects.create(
        user         = user,
        surah_number = result['surah'],
        ayah_number  = result['ayah'],
        audio_file   = audio_file_path,
        user_text    = result['user_text'],
        correct_text = result['correct_text'],
        score        = result['score']
    )