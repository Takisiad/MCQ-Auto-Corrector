from django.db import models
from accounts.models import User
from exams.models import Exam


class SubmissionStatus(models.TextChoices):
    PENDING    = 'PENDING',    'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    ERROR      = 'ERROR',      'Error'
    REVIEW     = 'REVIEW',     'Needs Review'
    VALIDATED  = 'VALIDATED',  'Validated'


class ExamSubmission(models.Model):
    exam            = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student         = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        limit_choices_to={'role': 'STUDENT'}
    )
    image_path      = models.CharField(max_length=500, blank=True)
    raw_answers     = models.JSONField(default=dict)
    machine_score   = models.FloatField(null=True, blank=True)
    manual_override = models.FloatField(null=True, blank=True)
    status          = models.CharField(
        max_length=15,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.PENDING
    )
    is_flagged      = models.BooleanField(default=False)
    flag_reason     = models.CharField(max_length=300, blank=True)
    confidence_scores = models.JSONField(default=dict)
    processed_at    = models.DateTimeField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.student.email} - {self.exam.title} - {self.status}'

    def final_grade(self):
        if self.manual_override is not None:
            return self.manual_override
        return self.machine_score