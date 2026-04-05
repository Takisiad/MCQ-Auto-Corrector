from rest_framework import serializers
from .models import Module, Exam, Question


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Question
        fields = ['id', 'order', 'correct_answer', 'weight']


class ExamSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model  = Exam
        fields = [
            'id', 'title', 'module',
            'teacher', 'created_at',
            'is_active', 'questions'
        ]
        read_only_fields = ['id', 'created_at', 'teacher']


class ExamCreateSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model  = Exam
        fields = ['id', 'title', 'module', 'questions']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        exam = Exam.objects.create(
            teacher=self.context['request'].user,
            **validated_data
        )
        for q in questions_data:
            Question.objects.create(exam=exam, **q)
        return exam


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Module
        fields = ['id', 'code', 'name', 'credit_hours', 'teacher']