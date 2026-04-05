from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Module, Exam, Question
from .serializers import (
    ExamSerializer,
    ExamCreateSerializer,
    ModuleSerializer
)


# ── Modules ───────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def module_list(request):
    if request.method == 'GET':
        modules    = Module.objects.all()
        serializer = ModuleSerializer(modules, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        if request.user.role not in ['ADMIN', 'TEACHER']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ModuleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ── Exams ─────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def exam_list(request):
    if request.method == 'GET':
        exams      = Exam.objects.filter(is_active=True)
        serializer = ExamSerializer(exams, many=True)
        return Response(serializer.data)

    if request.method == 'POST':
        if request.user.role not in ['ADMIN', 'TEACHER']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ExamCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            exam = serializer.save()
            return Response(
                ExamSerializer(exam).data,
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def exam_detail(request, exam_id):
    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return Response(
            {'error': 'Exam not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = ExamSerializer(exam)
        data       = serializer.data
        if request.user.role == 'STUDENT':
            for q in data['questions']:
                q.pop('correct_answer', None)
        return Response(data)

    if request.method == 'DELETE':
        if request.user.role not in ['ADMIN', 'TEACHER']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        exam.is_active = False
        exam.save()
        return Response(
            {'message': 'Exam deleted'},
            status=status.HTTP_200_OK
        )