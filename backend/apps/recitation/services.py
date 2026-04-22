import os
import difflib
import whisper
import re
from camel_tools.utils.normalize import (
    normalize_unicode,
    normalize_alef_ar,
    normalize_alef_maksura_ar,
    normalize_teh_marbuta_ar
)

#---------------------------- Whisper Model -----------------------

model = whisper.load_model("base")


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




