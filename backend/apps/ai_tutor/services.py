import os
import re
import requests
import chromadb
from groq import Groq
from sentence_transformers import CrossEncoder
from dotenv import load_dotenv

# from chromadb.utils import embedding_functions

# sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
#     model_name="all-MiniLM-L6-v2"
# )


# ===== CONFIGURATION =====
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HADITH_API_KEY = os.getenv("HADITH_API_KEY")
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

# ===== INITIALIZE CLIENTS =====
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_or_create_collection(name="islamic_knowledge")   #embedding_function=sentence_transformer_ef
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
groq_client = Groq(api_key=GROQ_API_KEY)

# ===========================
# PART 1 — DATA COLLECTION
# ===========================

def clean_text(text):
    cleaned = re.sub(r'<[^>]+>', '', text).strip()
    cleaned = cleaned.replace("God", "Allah")
    return cleaned

def fetch_chapter(chapter_number):
    response = requests.get(
        f"https://api.qurancdn.com/api/qdc/verses/by_chapter/{chapter_number}",
        params={
            "fields": "text_uthmani",
            "translations": "85",
            "per_page": "300"
        }
    )
    data = response.json()
    ayahs, ids, metadatas = [], [], []

    for verse in data['verses']:
        translation = clean_text(verse['translations'][0]['text'])
        arabic      = verse['text_uthmani']
        verse_key   = verse['verse_key']
        ayah_num    = verse_key.split(':')[1]

        # ayahs.append(translation)
        ayahs.append(arabic + " " + translation)
        ids.append(verse_key)
        metadatas.append({
            "surah_number": chapter_number,
            "ayah_number":  ayah_num,
            "arabic_text":  arabic,
            "source":       "Quran"
        })

    return ayahs, ids, metadatas


def fetch_hadiths(book_name, page=1):  # single page now
    response = requests.get(
        "https://hadithapi.com/api/hadiths/",
        params={
            "apiKey": HADITH_API_KEY,
            "book": book_name,
            "paginate": 25,
            "page": page
        }
    )
    data = response.json()
    hadiths = data['hadiths']['data']

    texts, ids, metas = [], [], []
    for hadith in hadiths:
        texts.append(str(hadith['hadithEnglish'] or ""))
        ids.append(f"{book_name}_{hadith['hadithNumber']}")
        metas.append({
            "source":        "Hadith",
            "collection":    str(hadith['book']['bookName'] or ""),
            "chapter":       str(hadith['chapter']['chapterEnglish'] or ""),
            "hadith_number": str(hadith['hadithNumber'] or ""),
            "narrator":      str(hadith['englishNarrator'] or ""),
            "arabic_text":   str(hadith['hadithArabic'] or ""),
            "status":        str(hadith['status'] or "Unknown")
        })

    return texts, ids, metas


def populate_database():
    import time

    existing_count = collection.count()
    print(f"Current documents in DB: {existing_count}")

    # ===== QURAN =====
    print("Checking Quran...")
    for surah in range(1, 115):
        existing = collection.get(ids=[f"{surah}:1"])
        if existing['ids']:
            continue  # already stored, skip silently
        try:
            texts, ids, metas = fetch_chapter(surah)
            collection.add(documents=texts, ids=ids, metadatas=metas)
            print(f"  Surah {surah}/114 stored ✅")
            time.sleep(2)
        except Exception as e:
            print(f"  Surah {surah} failed: {e}")
            continue

    # ===== HADITHS =====
    print("Checking Sahih Bukhari...")
    for page in range(1, 51):
        first_hadith_id = f"sahih-bukhari_{(page-1)*25+1}"
        existing = collection.get(ids=[first_hadith_id])
        if existing['ids']:
            continue

        try:
            texts, ids, metas = fetch_hadiths("sahih-bukhari", page=page)
            if texts:
                collection.add(documents=texts, ids=ids, metadatas=metas)
                print(f"  Bukhari page {page}/50 stored ✅")
            time.sleep(2)
        except Exception as e:
            print(f"  Bukhari page {page} failed, skipping")
            continue  # just skip, no retry

    print(f"\nDone! Total documents: {collection.count()} ✅")

# ===========================
# PART 2 — RAG PIPELINE
# ===========================

def rerank_results(query, documents, metadatas, top_k=3):
    pairs = [[query, doc] for doc in documents]
    scores = reranker.predict(pairs)
    ranked = sorted(
        zip(scores, documents, metadatas),
        key=lambda x: x[0],
        reverse=True
    )
    top_docs  = [doc  for _, doc,  _ in ranked[:top_k]]
    top_metas = [meta for _, _,    meta in ranked[:top_k]]
    return top_docs, top_metas


def ask_islamic_tutor(user_question, chat_history=None):
    if chat_history is None:
        chat_history = []

    # Step 1: Retrieve from ChromaDB
    results = collection.query(
        query_texts=[user_question],
        n_results=20,
        include=["documents", "metadatas"]
    )

    # Step 2: Rerank
    top_docs, top_metas = rerank_results(
        user_question,
        results["documents"][0],
        results["metadatas"][0]
    )

    # Step 3: Build context
    context = ""
    for i, (doc, meta) in enumerate(zip(top_docs, top_metas)):
        if meta["source"] == "Quran":
            context += f"""
Source {i+1}: Quran
Location: Surah {meta['surah_number']}, Ayah {meta['ayah_number']}
Arabic: {meta['arabic_text']}
English: {doc}
"""
        else:
            context += f"""
Source {i+1}: {meta['collection']}
Hadith #{meta['hadith_number']} | {meta['chapter']}
Narrator: {meta['narrator']}
Status: {meta['status']}
Text: {doc}
"""

    # Step 4: Append question with context to history
    chat_history.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {user_question}"
    })

    # Step 5: Send to Groq
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are an Islamic AI Tutor for QuranConnect platform.
RULES:
1. Answer ONLY from provided Quran and Hadith context
2. Always cite: Surah+Ayah for Quran, Hadith number+collection for Hadith
3. If context is insufficient, say honestly
4. Use respectful language (say ﷺ after Prophet's name)
5. Keep answers clear and scholarly"""
            },
            *chat_history
        ]
    )

    answer = response.choices[0].message.content

    # Step 6: Save answer to history
    chat_history.append({
        "role": "assistant",
        "content": answer
    })

    return answer, chat_history     