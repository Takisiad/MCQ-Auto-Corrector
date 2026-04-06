import logging
from celery import shared_task
from django.utils import timezone
from results.models import ExamSubmission, SubmissionStatus
from exams.models import Exam
from .processor import process_image

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def process_scan(self, submission_id: int, image_path: str):
    """
    Celery task — processes one scanned exam sheet.
    Called automatically after upload.

    Steps:
    1. Load submission from DB
    2. Load exam + answer key
    3. Run OMR processor (OpenCV)
    4. Save results back to DB
    """
    try:
        # get submission
        sub = ExamSubmission.objects.get(id=submission_id)
        sub.status = SubmissionStatus.PROCESSING
        sub.save()

        # get exam + questions
        exam      = Exam.objects.get(id=sub.exam.id)
        questions = list(exam.questions.all())

        # build bubble map from exam
        # in real use this comes from the exam PDF generator
        bubble_map = build_bubble_map(questions)

        # run OMR pipeline
        result = process_image(image_path, bubble_map, questions)

        # update student id if found in QR
        if result['student_id']:
            from accounts.models import User
            try:
                student = User.objects.get(student_id=result['student_id'])
                sub.student = student
            except User.DoesNotExist:
                pass

        # save results
        sub.raw_answers       = result['answers']
        sub.confidence_scores = result['confidences']
        sub.machine_score     = result['score']
        sub.is_flagged        = result['is_flagged']
        sub.flag_reason       = result['flag_reason']
        sub.status            = (
            SubmissionStatus.REVIEW
            if result['is_flagged']
            else SubmissionStatus.VALIDATED
        )
        sub.processed_at = timezone.now()
        sub.save()

        logger.info(
            f"[OMR] Done — submission {submission_id} "
            f"score={result['score']} flagged={result['is_flagged']}"
        )

        return {
            'status':    sub.status,
            'score':     result['score'],
            'is_flagged': result['is_flagged'],
        }

    except ExamSubmission.DoesNotExist:
        logger.error(f"[OMR] Submission {submission_id} not found")
        raise

    except Exception as exc:
        logger.error(f"[OMR] Failed — submission {submission_id}: {exc}")
        try:
            sub = ExamSubmission.objects.get(id=submission_id)
            sub.status      = SubmissionStatus.ERROR
            sub.flag_reason = str(exc)
            sub.save()
        except Exception:
            pass
        raise self.retry(exc=exc)


def build_bubble_map(questions: list) -> dict:
    """
    Build bubble coordinate map from exam questions.
    In production this is generated alongside the PDF.
    These coordinates match the printed exam sheet layout.

    A4 sheet at 300 DPI = 2480 x 3508 pixels
    Bubbles start at y=800, spacing=80px per question
    Options A-E spaced 120px apart starting at x=400
    """
    bubble_map = {}
    BUBBLE_W   = 40
    BUBBLE_H   = 40
    START_X    = 400
    START_Y    = 800
    Q_SPACING  = 80
    OPT_SPACING = 120
    OPTIONS    = ['A', 'B', 'C', 'D', 'E']

    for q in questions:
        q_key    = f"q{q.order}"
        y        = START_Y + (q.order - 1) * Q_SPACING
        options  = {}
        for i, opt in enumerate(OPTIONS):
            options[opt] = {
                "x": START_X + i * OPT_SPACING,
                "y": y,
                "w": BUBBLE_W,
                "h": BUBBLE_H,
            }
        bubble_map[q_key] = {"options": options}

    return bubble_map