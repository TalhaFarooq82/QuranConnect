# QuranConnect – Installation Guide

## 1. Project Overview

QuranConnect is a Django-based web application for Quran learning and peer tutoring.

The project currently contains these main modules:

- **Users** – student/tutor registration, login, profiles, tutor verification and password reset
- **Bookings** – students post tutoring jobs and tutors submit proposals
- **AI Tutor** – Quran/Hadith question answering using ChromaDB, retrieval/reranking and Groq
- **Recitation** – Arabic Quran recitation analysis using Whisper and Quran data from ChromaDB
- **Messaging** – real-time tutor/student chat using Django Channels and Redis
- **Payments** – wallet, escrow and Stripe wallet top-ups
- **Recommendations** – AI-based tutor/proposal scoring
- **Disputes** – dispute filing and dispute messaging
- **Notifications** – user notifications
- **Reviews** – tutor reviews/ratings

The project uses:

- Python
- Django
- PostgreSQL
- Django Channels + Redis
- ChromaDB
- Groq API
- Whisper
- Sentence Transformers / Cross Encoder
- Stripe
- Quran CDN API
- Hadith API

---

# 2. Prerequisites

Install the following before setting up QuranConnect.

### Required software

1. **Python 3.12 recommended**
2. **PostgreSQL**
3. **pgAdmin 4**
4. **Redis**
5. **FFmpeg** – required by Whisper for audio processing
6. **Git** – recommended for cloning the project

Verify Python:

```powershell
python --version
```

Verify PostgreSQL:

```powershell
psql --version
```

Verify FFmpeg:

```powershell
ffmpeg -version
```

Redis should be available on:

```text
127.0.0.1:6379
```

The current Django configuration uses this address by default.

---

# 3. Get the QuranConnect Project

Clone the project repository or copy the complete project folder to your computer.

Example:

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd QuranConnect
```

The Django project should contain the following important structure:

```text
QuranConnect/
│
├── apps/
│   ├── ai_tutor/
│   ├── bookings/
│   ├── disputes/
│   ├── messaging/
│   ├── notifications/
│   ├── payments/
│   ├── recitation/
│   ├── recommendations/
│   ├── reviews/
│   └── users/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── templates/
├── static/
├── media/
├── manage.py
└── ...
```

> **Important:** Make sure `manage.py` exists in the project root. If it is missing from a copied/archive version, obtain it from the project's main Git branch before continuing.

---

# 4. Create a Python Virtual Environment

Open PowerShell in the QuranConnect project directory.

For example:

```powershell
cd E:\QuranConnect
```

Create the virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
venv\Scripts\activate
```

After activation, the terminal should show something similar to:

```text
(venv) PS E:\QuranConnect>
```

---

# 5. Install Python Dependencies

Install the packages required by the project:

```powershell
pip install django
pip install daphne
pip install channels
pip install channels-redis
pip install psycopg2-binary
pip install python-dotenv
pip install whitenoise
pip install dj-database-url
pip install requests
pip install chromadb
pip install groq
pip install sentence-transformers
pip install stripe
pip install camel-tools
pip install openai-whisper
```

If the project already contains a `requirements.txt`, prefer:

```powershell
pip install -r requirements.txt
```

After installation, verify Django:

```powershell
python -m django --version
```

---

# 6. PostgreSQL Database Setup

QuranConnect uses PostgreSQL.

The local configuration in `config/settings.py` uses:

```text
Database: quranconnect_db
User: postgres
Host: localhost
Port: 5432
```

Create a PostgreSQL database named:

```text
quranconnect_db
```

This can be done through pgAdmin 4.

### Using pgAdmin 4

1. Open **pgAdmin 4**.
2. Expand **Servers**.
3. Expand your PostgreSQL server.
4. Right-click **Databases**.
5. Select **Create → Database**.
6. Set the database name to:

```text
quranconnect_db
```

7. Save.

---

# 7. Restore the QuranConnect Database

If a PostgreSQL backup is provided, restore it using **pgAdmin 4**.

## Important

A PostgreSQL backup must be restored into **PostgreSQL**.

Do **not** import a PostgreSQL backup into MySQL/MySQL Workbench.

### For a Custom-format backup

1. Open pgAdmin 4.
2. Create/select the `quranconnect_db` database.
3. Right-click `quranconnect_db`.
4. Select **Restore...**
5. Select the `.backup` / custom-format backup file.
6. Choose the appropriate format if pgAdmin asks.
7. Start the restore.
8. Refresh the database after completion.

### For a Plain SQL backup

A plain PostgreSQL SQL dump should also be executed/restored using PostgreSQL tools, not MySQL.

In pgAdmin:

1. Select the PostgreSQL database.
2. Open **Query Tool**.
3. Open the plain `.sql` backup.
4. Execute it.

For a large SQL dump, using PostgreSQL's restore/import tools may be more reliable than opening the entire file in the Query Tool.

---

# 8. Configure Django Database Settings

Open:

```text
config/settings.py
```

The current local project configuration expects PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'quranconnect_db',
        'USER': 'postgres',
        'PASSWORD': '<YOUR_POSTGRES_PASSWORD>',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Replace the PostgreSQL password with the password configured on the local PostgreSQL installation.

### Security note

Do not commit real passwords, API keys, Stripe keys, email passwords or other secrets to GitHub.

Use environment variables for sensitive values.

---

# 9. Environment Variables

QuranConnect reads several values from environment variables.

Create a `.env` file in the Django project root if it is not already present:

```text
QuranConnect/
├── .env
├── manage.py
├── config/
└── apps/
```

Example:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

GROQ_API_KEY=your-groq-api-key
HADITH_API_KEY=your-hadith-api-key

STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key

EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-app-password

REDIS_URL=redis://127.0.0.1:6379

CSRF_TRUSTED_ORIGINS=https://*.up.railway.app
```

For production, also configure:

```env
DATABASE_URL=your-production-postgresql-connection-url
```

The project uses `DATABASE_URL` when it is present.

---

# 10. Groq API

The AI Tutor uses the Groq API.

The current implementation uses:

```text
llama-3.3-70b-versatile
```

Set:

```env
GROQ_API_KEY=your-groq-api-key
```

Without a valid Groq API key, the AI Tutor cannot generate answers.

---

# 11. Hadith API

The AI Tutor population process retrieves Hadith data from the Hadith API.

Set:

```env
HADITH_API_KEY=your-hadith-api-key
```

The Quran data is retrieved from the Quran CDN API.

---

# 12. ChromaDB Setup

QuranConnect's AI Tutor and Recitation features use a persistent ChromaDB database.

The project expects ChromaDB at:

```text
apps/ai_tutor/chroma_db/
```

The collection name is:

```text
islamic_knowledge
```

The same collection is used by the recitation feature.

### Important

`chroma_db` is **not the PostgreSQL database**.

There are two separate data stores:

```text
PostgreSQL
    ↓
Django application data
(users, jobs, proposals, messages, wallets, reviews, etc.)

ChromaDB
    ↓
Quran/Hadith knowledge used by AI Tutor and Recitation
```

If the project already contains a populated:

```text
apps/ai_tutor/chroma_db/
```

directory, keep it.

Do not delete it unless you intentionally want to rebuild the Quran/Hadith vector database.

---

# 13. Populate ChromaDB if Required

If `apps/ai_tutor/chroma_db/` is empty or the `islamic_knowledge` collection does not contain the required data, use the project's Django management command:

```powershell
python manage.py populate_quran
```

This command calls the `populate_database()` function.

It:

1. Checks existing ChromaDB documents.
2. Downloads Quran chapters.
3. Stores Quran Arabic text and English translation.
4. Downloads Sahih Bukhari pages.
5. Stores Hadith metadata.
6. Avoids adding entries that already exist.
7. Prints the final ChromaDB document count.

The process requires:

- Internet access
- `GROQ_API_KEY` is not required for population itself
- `HADITH_API_KEY` is required for Hadith population
- sufficient disk space

After completion, the application should report a non-zero ChromaDB document count.

---

# 14. Django Migrations

After PostgreSQL is configured, run:

```powershell
python manage.py makemigrations
```

Then:

```powershell
python manage.py migrate
```

If you restored an existing complete PostgreSQL database backup, first check the database and migration state before creating new migrations.

For a normal fresh installation, use:

```powershell
python manage.py migrate
```

The project contains migrations for:

- users
- bookings
- payments
- AI Tutor
- recitation
- messaging
- recommendations
- disputes
- notifications
- reviews

---

# 15. Create an Admin User

Create a Django superuser:

```powershell
python manage.py createsuperuser
```

Enter:

```text
Username
Email
Password
```

Then the Django admin panel can be accessed at:

```text
http://127.0.0.1:8000/admin/
```

---

# 16. Static Files

For local development, Django can serve the static files from the configured static directories.

For production, collect static files:

```powershell
python manage.py collectstatic
```

The project uses WhiteNoise for serving static files in deployment.

---

# 17. Media Files

User-generated files are stored under:

```text
media/
```

The project includes media for things such as:

- profile images
- avatars
- tutor certifications
- CNIC images
- dispute evidence
- chat files
- recitation audio
- AI Tutor uploads

When moving QuranConnect to another computer, copy the required `media/` directory if existing uploaded files need to be preserved.

The PostgreSQL database does **not** automatically contain the actual uploaded media files.

---

# 18. Redis Setup

Django Channels is used for real-time messaging and WebSocket functionality.

The project uses:

```text
redis://127.0.0.1:6379
```

by default.

Start Redis before running the application.

Check that Redis is available on:

```text
127.0.0.1:6379
```

If using another Redis server, set:

```env
REDIS_URL=redis://<HOST>:<PORT>
```

---

# 19. Run QuranConnect

Make sure the virtual environment is activated:

```powershell
venv\Scripts\activate
```

Start Redis first.

Then run Django.

For normal HTTP development:

```powershell
python manage.py runserver
```

For the project's ASGI/WebSocket configuration, Daphne can be used:

```powershell
daphne config.asgi:application
```

The application should then be available at:

```text
http://127.0.0.1:8000/
```

---

# 20. Test the Main Features

After starting the application, test the following.

## User System

- Register as a student
- Register as a tutor
- Login/logout
- Profile management
- Tutor certification/verification
- Password reset

## Tutoring/Bookings

- Student posts a tutoring job
- Tutor browses available jobs
- Tutor submits a proposal
- Student views proposals
- Student awards a proposal
- Job status changes appropriately

## Messaging

- Open a conversation
- Send a text message
- Send files
- Test real-time message delivery
- Test video signaling if enabled

Redis must be running for the WebSocket functionality.

## AI Tutor

- Open AI Tutor
- Ask a Quran/Hadith question
- Verify that the answer uses retrieved Quran/Hadith context
- Verify source citations in the response
- Test chat history
- Test shared chat functionality if required

ChromaDB must contain the `islamic_knowledge` collection.

## Recitation

- Record/upload a Quran recitation
- Verify Whisper transcription
- Verify ayah matching
- Verify word-level feedback
- Verify recitation score

Whisper requires FFmpeg and its model files.

## Payments

- Test wallet functionality
- Test Stripe checkout using Stripe test credentials
- Test escrow flow
- Test payment release

Use Stripe test keys during development.

## Disputes

- File a dispute
- Upload evidence if required
- Send dispute messages
- Test dispute status changes

## Reviews

- Complete a tutoring job
- Submit a tutor review/rating
- Verify the review appears correctly

---

# 21. Common Problems

## Problem: `python` is not recognized

Install Python and make sure it is added to PATH.

Then reopen PowerShell.

---

## Problem: `No module named django`

Activate the virtual environment:

```powershell
venv\Scripts\activate
```

Then install Django/dependencies.

---

## Problem: PostgreSQL connection error

Check:

```text
PostgreSQL service is running
Database name is correct
Username is correct
Password is correct
Host is localhost
Port is 5432
```

The expected local database is:

```text
quranconnect_db
```

---

## Problem: PostgreSQL backup does not import into MySQL

This is expected.

QuranConnect uses PostgreSQL.

Do not use:

```text
MySQL Workbench
mysql.exe
```

to restore the PostgreSQL backup.

Use:

```text
pgAdmin 4
```

and restore the backup into PostgreSQL.

---

## Problem: ChromaDB is empty

Check:

```text
apps/ai_tutor/chroma_db/
```

If it is empty, restore the backed-up ChromaDB directory or rebuild it using:

```powershell
python manage.py populate_quran
```

Do not confuse ChromaDB with PostgreSQL.

---

## Problem: AI Tutor does not answer

Check:

```env
GROQ_API_KEY=...
```

Also check that:

```text
apps/ai_tutor/chroma_db/
```

contains the `islamic_knowledge` collection.

---

## Problem: Hadith data does not populate

Check:

```env
HADITH_API_KEY=...
```

and make sure the computer has Internet access.

---

## Problem: Real-time chat does not work

Check that Redis is running and that:

```env
REDIS_URL=redis://127.0.0.1:6379
```

is correct.

Also run the application through the ASGI configuration when WebSockets are required.

---

## Problem: Recitation analysis fails

Check:

```powershell
ffmpeg -version
```

Also make sure Whisper is installed and that its required model has been downloaded.

The current project loads:

```text
Whisper base model
```

---

## Problem: Uploaded images/files are missing

Copy the project's:

```text
media/
```

directory.

Database restoration alone does not restore the physical files stored in `MEDIA_ROOT`.

---

# 22. Fresh Installation Order

For a completely fresh machine, the recommended order is:

```text
1. Install Python
        ↓
2. Install PostgreSQL + pgAdmin 4
        ↓
3. Install Redis
        ↓
4. Install FFmpeg
        ↓
5. Copy/clone QuranConnect
        ↓
6. Create Python virtual environment
        ↓
7. Activate virtual environment
        ↓
8. Install Python dependencies
        ↓
9. Create quranconnect_db in PostgreSQL
        ↓
10. Configure PostgreSQL credentials
        ↓
11. Restore PostgreSQL database backup (if available)
        ↓
12. Configure .env/API keys
        ↓
13. Preserve/restore apps/ai_tutor/chroma_db
        ↓
14. Restore media/ if existing files are required
        ↓
15. Run Django migrations if needed
        ↓
16. Create superuser if needed
        ↓
17. Start Redis
        ↓
18. Start Django/Daphne
        ↓
19. Open http://127.0.0.1:8000/
        ↓
20. Test QuranConnect features
```

---

# 23. Important Backup Information

For a complete QuranConnect backup, keep **all three** of the following separately:

### A. PostgreSQL database backup

Contains Django database records such as:

- users
- profiles
- jobs
- proposals
- conversations
- messages
- wallets
- transactions
- disputes
- reviews
- AI Tutor chat records
- recitation records
- recommendation scores
- notifications

### B. ChromaDB

Keep:

```text
apps/ai_tutor/chroma_db/
```

This contains the persistent Quran/Hadith vector database used by the AI Tutor and Recitation features.

### C. Media

Keep:

```text
media/
```

This contains uploaded files such as profile pictures, certificates, chat files and recitation audio.

A PostgreSQL backup by itself is therefore **not a complete QuranConnect backup**.

---

# 24. Production / Railway Notes

QuranConnect can use a production PostgreSQL database through:

```env
DATABASE_URL=...
```

The settings file automatically switches to the `DATABASE_URL` configuration when it is present.

Production should also configure:

```env
SECRET_KEY=...
DEBUG=False
DATABASE_URL=...
GROQ_API_KEY=...
HADITH_API_KEY=...
STRIPE_PUBLIC_KEY=...
STRIPE_SECRET_KEY=...
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
REDIS_URL=...
CSRF_TRUSTED_ORIGINS=...
```

Do not use development credentials or real secrets in source control.

For Railway deployment, configure the required environment variables in the Railway service rather than committing `.env` to GitHub.

---

# 25. Security Checklist

Before sharing or deploying the project:

- [ ] Remove real API keys from source code
- [ ] Remove real email passwords from source code
- [ ] Do not commit `.env`
- [ ] Use a strong Django `SECRET_KEY`
- [ ] Set `DEBUG=False` in production
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Configure `CSRF_TRUSTED_ORIGINS`
- [ ] Use Stripe test keys during testing
- [ ] Keep PostgreSQL backups secure
- [ ] Keep ChromaDB backups secure
- [ ] Keep uploaded media backups secure
- [ ] Never commit private user documents or CNIC images to a public repository

---

# 26. Quick Start

For a machine that already has PostgreSQL, Redis and FFmpeg installed:

```powershell
cd E:\QuranConnect

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate

python manage.py populate_quran

python manage.py createsuperuser

daphne config.asgi:application
```

Then open:

```text
http://127.0.0.1:8000/
```

If a populated ChromaDB backup is already available, do **not** run the population command unnecessarily. Preserve the existing:

```text
apps/ai_tutor/chroma_db/
```

directory.

---

# 27. Final Verification Checklist

Before considering the installation complete:

- [ ] Python environment activates successfully
- [ ] All Python dependencies are installed
- [ ] PostgreSQL is running
- [ ] `quranconnect_db` exists
- [ ] Database backup has been restored if required
- [ ] Django migrations are applied
- [ ] `.env` is configured
- [ ] Groq API key works
- [ ] Hadith API key works
- [ ] Redis is running
- [ ] FFmpeg is available
- [ ] ChromaDB exists and contains `islamic_knowledge`
- [ ] Media files are present if required
- [ ] Django starts successfully
- [ ] Login/registration works
- [ ] Tutoring workflow works
- [ ] Real-time messaging works
- [ ] AI Tutor works
- [ ] Quran recitation analysis works
- [ ] Payments work with Stripe test credentials
- [ ] Disputes work
- [ ] Reviews work
- [ ] Notifications work

---

## QuranConnect Architecture Summary

```text
                         QuranConnect
                              │
             ┌────────────────┼────────────────┐
             │                │                │
          Django           PostgreSQL        Redis
             │                │                │
     ┌───────┼───────┐        │          WebSockets
     │       │       │        │
   Users  Bookings  AI       Django
     │       │     Tutor       Data
     │       │       │
     │       │   ChromaDB
     │       │       │
     │       │   Quran/Hadith
     │       │
     │    Payments ── Stripe
     │
     ├── Recitation ── Whisper
     ├── Messaging ─── Channels
     ├── Disputes
     ├── Notifications
     ├── Reviews
     └── Recommendations
```

This guide is intended for setting up the QuranConnect FYP locally and for preparing the project for deployment.
