import logging
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

logger = logging.getLogger(__name__)

def _env_int(name, default):
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


def _env_float(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_TEMPERATURE = _env_float("GROQ_TEMPERATURE", 0.2)
GROQ_MAX_TOKENS = _env_int("GROQ_MAX_TOKENS", 1200)
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
HADITH_API_KEY = os.getenv("HADITH_API_KEY")
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
API_TIMEOUT_SECONDS = 20
MAX_QUESTION_LENGTH = 2000
RETRIEVAL_RESULT_COUNT = 20
RERANK_RESULT_COUNT = 3
QURAN_CHAPTER_API_URL = "https://api.qurancdn.com/api/qdc/verses/by_chapter/{chapter_number}"
HADITH_API_URL = HADITH_API_URL

# ===== INITIALIZE CLIENTS =====
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection = chroma_client.get_or_create_collection(name="islamic_knowledge")   #embedding_function=sentence_transformer_ef
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
_groq_client = None


def get_groq_client():
    """Create the Groq client only when an AI request is made."""
    global _groq_client

    if _groq_client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not configured.")

        _groq_client = Groq(api_key=GROQ_API_KEY)

    return _groq_client

# ===========================
# PART 1 — DATA COLLECTION
# ===========================

def clean_text(text):
    cleaned = re.sub(r'<[^>]+>', '', text).strip()
    cleaned = cleaned.replace("God", "Allah")
    return cleaned

def fetch_chapter(chapter_number):
    try:
        chapter_number = int(chapter_number)
    except (TypeError, ValueError) as error:
        raise ValueError("Chapter number must be an integer.") from error

    if not 1 <= chapter_number <= 114:
        raise ValueError("Chapter number must be between 1 and 114.")

    response = requests.get(
        QURAN_CHAPTER_API_URL.format(chapter_number=chapter_number),
        params={
            "fields": "text_uthmani",
            "translations": "85",
            "per_page": "300"
        },
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    verses = data.get("verses")

    if not isinstance(verses, list):
        raise ValueError("Quran API returned an invalid verses response.")

    ayahs, ids, metadatas = [], [], []

    for verse in verses:
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


def fetch_hadiths(book_name, page=1):
    book_name = str(book_name or "").strip()

    if not book_name:
        raise ValueError("Hadith book name is required.")

    try:
        page = int(page)
    except (TypeError, ValueError) as error:
        raise ValueError("Hadith page must be an integer.") from error

    if page < 1:
        raise ValueError("Hadith page must be greater than zero.")

    if not HADITH_API_KEY:
        raise RuntimeError("HADITH_API_KEY is not configured.")

    response = requests.get(
        "https://hadithapi.com/api/hadiths/",
        params={
            "apiKey": HADITH_API_KEY,
            "book": book_name,
            "paginate": 25,
            "page": page
        },
        timeout=API_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data = response.json()
    hadith_container = data.get("hadiths", {})
    hadiths = hadith_container.get("data")

    if not isinstance(hadiths, list):
        raise ValueError("Hadith API returned an invalid data response.")

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
    logger.info("Current documents in DB: %s", existing_count)

    # ===== QURAN =====
    logger.info("Checking Quran knowledge documents")
    for surah in range(1, 115):
        existing = collection.get(ids=[f"{surah}:1"])
        if existing['ids']:
            continue  # already stored, skip silently
        try:
            texts, ids, metas = fetch_chapter(surah)
            collection.add(documents=texts, ids=ids, metadatas=metas)
            logger.info("Stored Surah %s/114", surah)
            time.sleep(2)
        except Exception as e:
            logger.exception("Failed to store Surah %s", surah)
            continue

    # ===== HADITHS =====
    logger.info("Checking Sahih Bukhari documents")
    for page in range(1, 51):
        first_hadith_id = f"sahih-bukhari_{(page-1)*25+1}"
        existing = collection.get(ids=[first_hadith_id])
        if existing['ids']:
            continue

        try:
            texts, ids, metas = fetch_hadiths("sahih-bukhari", page=page)
            if texts:
                collection.add(documents=texts, ids=ids, metadatas=metas)
                logger.info("Stored Bukhari page %s/50", page)
            time.sleep(2)
        except Exception as e:
            logger.exception("Failed to store Bukhari page %s", page)
            continue  # just skip, no retry

    logger.info("Knowledge population complete: %s documents", collection.count())

# ===========================
# PART 2 — RAG PIPELINE
# ===========================

def rerank_results(query, documents, metadatas, top_k=3):
    if not documents or not metadatas:
        return [], []

    result_count = min(len(documents), len(metadatas))
    documents = documents[:result_count]
    metadatas = metadatas[:result_count]

    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        top_k = 3

    top_k = max(1, min(top_k, result_count))

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


def extract_query_results(results):
    """Return the first document and metadata batches safely."""
    if not isinstance(results, dict):
        return [], []

    document_batches = results.get("documents") or []
    metadata_batches = results.get("metadatas") or []

    documents = (
        document_batches[0]
        if document_batches and isinstance(document_batches[0], list)
        else []
    )
    metadatas = (
        metadata_batches[0]
        if metadata_batches and isinstance(metadata_batches[0], list)
        else []
    )

    return documents, metadatas


def build_context(documents, metadatas):
    """Format retrieved documents while tolerating missing metadata."""
    context_parts = []

    for index, (document, metadata) in enumerate(
        zip(documents, metadatas),
        start=1,
    ):
        metadata = metadata or {}
        source = metadata.get("source", "Unknown")

        if source == "Quran":
            context_parts.append(
                f"Source {index}: Quran\n"
                f"Location: Surah {metadata.get('surah_number', 'Unknown')}, "
                f"Ayah {metadata.get('ayah_number', 'Unknown')}\n"
                f"Arabic: {metadata.get('arabic_text', '')}\n"
                f"English: {document}"
            )
        else:
            context_parts.append(
                f"Source {index}: "
                f"{metadata.get('collection', source)}\n"
                f"Hadith #{metadata.get('hadith_number', 'Unknown')} | "
                f"{metadata.get('chapter', 'Unknown')}\n"
                f"Narrator: {metadata.get('narrator', 'Unknown')}\n"
                f"Status: {metadata.get('status', 'Unknown')}\n"
                f"Text: {document}"
            )

    return "\n\n".join(context_parts)


def extract_groq_answer(response):
    """Extract non-empty answer text from a Groq completion."""
    choices = getattr(response, "choices", None)

    if not choices:
        raise ValueError("Groq returned no completion choices.")

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None)

    if content is None:
        raise ValueError("Groq returned a completion without content.")

    answer = str(content).strip()

    if not answer:
        raise ValueError("Groq returned an empty answer.")

    return answer


def ask_islamic_tutor(user_question, chat_history=None):
    user_question = str(user_question or "").strip()

    if not user_question:
        raise ValueError("A tutor question is required.")

    if len(user_question) > MAX_QUESTION_LENGTH:
        raise ValueError(
            f"Tutor questions cannot exceed {MAX_QUESTION_LENGTH} characters."
        )

    chat_history = list(chat_history or [])

    # Step 1: Retrieve from ChromaDB
    results = collection.query(
        query_texts=[user_question],
        n_results=RETRIEVAL_RESULT_COUNT,
        include=["documents", "metadatas"]
    )

    # Step 2: Rerank
    documents, metadatas = extract_query_results(results)

    top_docs, top_metas = rerank_results(
        user_question,
        documents,
        metadatas,
        top_k=RERANK_RESULT_COUNT,
    )

    # Step 3: Build context
    context = build_context(top_docs, top_metas)

    # Step 4: Append question with context to history
    chat_history.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {user_question}"
    })

    # Step 5: Send to Groq
    response = get_groq_client().chat.completions.create(
        model=GROQ_MODEL,
        temperature=GROQ_TEMPERATURE,
        max_tokens=GROQ_MAX_TOKENS,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            *chat_history
        ]
    )

    answer = extract_groq_answer(response)

    # Step 6: Save answer to history
    chat_history.append({
        "role": "assistant",
        "content": answer
    })

    return answer, chat_history     