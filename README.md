# MCQ Auto Corrector

Automatic exam correction system using OMR (Optical Mark Recognition).

**Stack:** Django · CouchDB · Celery · OpenCV · ReportLab · SvelteKit

---

## What This Project Does

1. Teacher creates an exam with MCQ questions and answer key
2. System generates a printable PDF with QR code + bubble grid + anchor markers
3. Students fill bubbles on paper
4. Teacher scans all papers and uploads the PDF
5. System automatically:
   - Splits PDF into individual pages
   - Deskews each image using anchor markers
   - Reads QR code to identify exam and student
   - Detects which bubble is filled (A/B/C/D/E)
   - Calculates score against answer key
   - Flags ambiguous results for teacher review
6. Students view their grades online

---

## Setup — Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

## Setup — Mac / Linux / Kali
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

---

## Requirements

- Python 3.11+
- CouchDB 3.x → localhost:5984 (user: admin / pass: admin)
- Redis → localhost:6379

### Install CouchDB
- Windows/Mac: https://couchdb.apache.org/
- Linux: `sudo apt install couchdb`

### Install Redis
- Windows: https://github.com/microsoftarchive/redis/releases
- Mac: `brew install redis`
- Linux: `sudo apt install redis-server`

---

## API Endpoints

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| POST | /api/auth/login/ | Login → JWT token | No |
| POST | /api/auth/register/ | Register user | No |
| GET  | /api/auth/profile/ | Current user info | Yes |
| GET  | /api/auth/users/ | All users | Admin only |
| GET  | /api/exams/ | List all exams | Yes |
| POST | /api/exams/ | Create exam + questions | Teacher/Admin |
| GET  | /api/exams/{id}/ | Get exam detail | Yes |
| DELETE | /api/exams/{id}/ | Delete exam | Teacher/Admin |
| GET  | /api/exams/modules/ | List modules | Yes |
| POST | /api/exams/modules/ | Create module | Teacher/Admin |
| POST | /api/results/upload/{exam_id}/ | Upload bulk scans | Teacher/Admin |
| GET  | /api/results/ | List submissions | Yes |
| GET  | /api/results/{id}/ | Submission detail | Yes |
| PATCH | /api/results/{id}/override/ | Manual grade override | Teacher/Admin |
| GET  | /api/results/stats/{exam_id}/ | Exam statistics | Teacher/Admin |

---

## Project Structure
qcmcorector/
├── config/
│   ├── settings.py        → Django + CouchDB + Celery config
│   ├── urls.py            → main routes
│   └── celery.py          → async task runner
├── accounts/
│   ├── models.py          → User (Admin/Teacher/Student)
│   ├── serializers.py     → JSON conversion
│   ├── views.py           → register, login, profile
│   └── urls.py            → auth routes
├── exams/
│   ├── models.py          → Module, Exam, Question
│   ├── serializers.py     → JSON conversion
│   ├── views.py           → CRUD API
│   ├── pdf_generator.py   → generate exam PDF
│   └── urls.py            → exam routes
├── omr/
│   ├── processor.py       → OpenCV pipeline
│   └── tasks.py           → Celery background task
├── results/
│   ├── models.py          → ExamSubmission
│   ├── serializers.py     → JSON conversion
│   ├── views.py           → grades, upload, stats
│   └── urls.py            → results routes
├── manage.py
└── requirements.txt

---

## Build Progress

- [x] accounts — User model (Admin/Teacher/Student)
- [x] accounts — Login, register, profile API
- [x] exams — Module + Exam + Question models
- [x] exams — Full CRUD API
- [x] exams — PDF generator (QR + bubble grid + anchors)
- [x] omr — OpenCV deskew + anchor detection
- [x] omr — QR code reader
- [x] omr — Bubble density detection + confidence scoring
- [x] omr — Celery background task
- [x] results — ExamSubmission model
- [x] results — Upload scans API
- [x] results — Grade override API
- [x] results — Exam statistics API
- [ ] frontend — SvelteKit UI

---

## OMR Pipeline
Upload PDF scan
↓
Split into page images (pdf2image)
↓
Detect anchor markers → deskew (OpenCV)
↓
Read QR code → get exam ID + student ID
↓
For each question:
scan bubbles → calculate fill density
pick highest filled bubble = answer
↓
Confidence check (threshold 85%)

= 85% → auto validate
< 85%  → flag for teacher review
↓
Calculate score against answer key
↓
Save to database


---

## Team

- Backend: Django REST API + OMR Engine
- Frontend: SvelteKit (in progress)