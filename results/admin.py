from django.contrib import admin
from .models import ExamSubmission


@admin.register(ExamSubmission)
class ExamSubmissionAdmin(admin.ModelAdmin):
    list_display  = ['student', 'exam', 'status', 'machine_score', 'manual_override', 'is_flagged']
    list_filter   = ['status', 'is_flagged', 'exam']
    search_fields = ['student__email', 'exam__title']