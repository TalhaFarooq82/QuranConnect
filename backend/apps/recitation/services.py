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

#Whisper Model 

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

def find_ayah_by_arabic(clean_user_text):
    # Get ALL Quran ayahs from ChromaDB
    all_ayahs = collection.get(
        where   = {"source": "Quran"},
        include = ["metadatas"]
    )

    best_score = 0
    best_meta  = None
    best_clean = None

    for meta in all_ayahs['metadatas']:
        arabic  = meta['arabic_text']
        cleaned = clean_whisper_output(arabic)
        score   = difflib.SequenceMatcher(None, cleaned, clean_user_text).ratio()

        if score > best_score:
            best_score = score
            best_meta  = meta
            best_clean = cleaned

    return best_meta, best_clean, best_score
def analyze_recitation(audio_file):

    print("=== analyze_recitation started ===")

    try:
        print("Step 1: Starting Whisper transcription...")
        result = model.transcribe(audio_file, language="ar")
        print("✅ Whisper transcription finished")

        user_text = result["text"]
        print(f"User text: {user_text}")

        print("Step 2: Cleaning text...")
        clean_user = clean_whisper_output(user_text)
        print(f"Cleaned: {clean_user}")

        print("Step 3: Searching matching ayah...")
        best_meta, best_clean, best_score = find_ayah_by_arabic(clean_user)
        print(f"Best score: {best_score}")

        if best_meta is None:
            print("❌ No matching ayah found")
            return {"error": "No matching ayah found"}

        print("Step 4: Comparing words...")
        feedback = compare_words(best_clean, clean_user)

        total = len(feedback)
        correct = sum(1 for f in feedback if f["status"] == "correct")
        score = round((correct / total) * 100) if total > 0 else 0

        print(f"Final score: {score}")

        return {
            "surah": best_meta["surah_number"],
            "ayah": best_meta["ayah_number"],
            "correct_text": best_meta["arabic_text"],
            "user_text": user_text,
            "feedback": feedback,
            "score": score,
        }

    except Exception as e:
        print("❌ ERROR inside analyze_recitation:", e)
        raise
 

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
