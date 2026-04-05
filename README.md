# MCQ Auto Corrector

Automatic exam correction system using OMR (Optical Mark Recognition).

**Stack:** Django · CouchDB · Celery · OpenCV · SvelteKit

---

## Setup — Windows

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

## Setup — Mac / Linux

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

---

## API Endpoints

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| POST | /api/auth/login/ | Login → JWT token | No |
| POST | /api/auth/register/ | Register user | No |
| GET  | /api/auth/profile/ | Current user | Yes |
| GET  | /api/auth/users/ | All users | Admin |
| GET  | /api/exams/ | List exams | Yes |
| POST | /api/exams/ | Create exam | Teacher/Admin |
| GET  | /api/exams/modules/ | List modules | Yes |
| POST | /api/exams/modules/ | Create module | Teacher/Admin |

---

## Progress
- [x] accounts — User model (Admin/Teacher/Student)
- [x] accounts — Login, register, profile API
- [x] exams — Module + Exam + Question models
- [x] exams — Full CRUD API
- [ ] results — ExamSubmission, grades
- [ ] omr — OpenCV OMR pipeline
- [ ] frontend — SvelteKit
# MCQ-Auto-Corrector
