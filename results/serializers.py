from rest_framework import serializers
from .models import ExamSubmission


class ExamSubmissionSerializer(serializers.ModelSerializer):
    final_grade = serializers.SerializerMethodField()

    class Meta:
        model  = ExamSubmission
        fields = [
            'id', 'exam', 'student',
            'machine_score', 'manual_override',
            'final_grade', 'status',
            'is_flagged', 'flag_reason',
            'raw_answers', 'confidence_scores',
            'processed_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'machine_score', 'status',
            'is_flagged', 'processed_at', 'created_at'
        ]

    def get_final_grade(self, obj):
        return obj.final_grade()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.role == 'STUDENT':
            data.pop('raw_answers', None)
            data.pop('confidence_scores', None)
            data.pop('image_path', None)
        return data