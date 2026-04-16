import os
from pathlib import Path

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone

from .models import ExamSubmission, SubmissionStatus
from .serializers import ExamSubmissionSerializer
from exams.models import Exam
from omr.tasks import process_scan


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def submission_list(request):
    user = request.user

    if user.role == 'STUDENT':
        submissions = ExamSubmission.objects.filter(student=user)
    elif user.role == 'TEACHER':
        submissions = ExamSubmission.objects.filter(exam__teacher=user)
    else:
        submissions = ExamSubmission.objects.all()

    # optional filters
    exam_id = request.query_params.get('exam_id')
    flagged = request.query_params.get('flagged')
    if exam_id:
        submissions = submissions.filter(exam_id=exam_id)
    if flagged == 'true':
        submissions = submissions.filter(is_flagged=True)

    serializer = ExamSubmissionSerializer(
        submissions, many=True,
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def submission_detail(request, sub_id):
    try:
        sub = ExamSubmission.objects.get(id=sub_id)
    except ExamSubmission.DoesNotExist:
        return Response(
            {'error': 'Submission not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.user.role == 'STUDENT' and sub.student != request.user:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    serializer = ExamSubmissionSerializer(
        sub, context={'request': request}
    )
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def override_grade(request, sub_id):
    if request.user.role not in ['ADMIN', 'TEACHER']:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        sub = ExamSubmission.objects.get(id=sub_id)
    except ExamSubmission.DoesNotExist:
        return Response(
            {'error': 'Submission not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    new_score = request.data.get('manual_override')
    if new_score is None:
        return Response(
            {'error': 'manual_override is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    sub.manual_override = float(new_score)
    sub.status          = SubmissionStatus.VALIDATED
    sub.is_flagged      = False
    sub.processed_at    = timezone.now()
    sub.save()

    return Response({
        'id':              sub.id,
        'manual_override': sub.manual_override,
        'final_grade':     sub.final_grade(),
        'status':          sub.status,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def exam_statistics(request, exam_id):
    if request.user.role not in ['ADMIN', 'TEACHER']:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    submissions = ExamSubmission.objects.filter(
        exam_id=exam_id,
        status=SubmissionStatus.VALIDATED
    )

    if not submissions.exists():
        return Response({'message': 'No validated submissions yet'})

    grades  = [s.final_grade() for s in submissions if s.final_grade() is not None]
    average = sum(grades) / len(grades) if grades else 0

    try:
        exam        = Exam.objects.get(id=exam_id)
        total_marks = sum(q.weight for q in exam.questions.all())
    except Exam.DoesNotExist:
        total_marks = 0

    pass_threshold = total_marks * 0.5
    passed  = len([g for g in grades if g >= pass_threshold])
    failed  = len(grades) - passed

    return Response({
        'exam_id':        exam_id,
        'total_students': len(grades),
        'average_score':  round(average, 2),
        'highest_score':  round(max(grades), 2) if grades else 0,
        'lowest_score':   round(min(grades), 2) if grades else 0,
        'passed':         passed,
        'failed':         failed,
        'pass_rate':      round((passed / len(grades)) * 100, 1) if grades else 0,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_scans(request, exam_id):
    if request.user.role not in ['ADMIN', 'TEACHER']:
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        exam = Exam.objects.get(id=exam_id)
    except Exam.DoesNotExist:
        return Response(
            {'error': 'Exam not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    file = request.FILES.get('scans')
    if not file:
        return Response(
            {'error': 'No file uploaded'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # save uploaded file
    upload_dir = Path(settings.MEDIA_ROOT) / 'scans' / str(exam_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.name

    with open(file_path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)

    # split PDF into images
    image_paths = split_pdf(file_path, upload_dir)

    # create one submission per image and queue Celery task
    # student is left null — it will be filled from the QR code during processing
    submission_ids = []
    for img_path in image_paths:
        sub = ExamSubmission.objects.create(
            exam       = exam,
            image_path = str(img_path),
            status     = SubmissionStatus.PENDING,
        )
        process_scan.delay(sub.id, str(img_path))
        submission_ids.append(sub.id)

    return Response({
        'message':        f'{len(submission_ids)} scans queued',
        'submission_ids': submission_ids,
    }, status=status.HTTP_202_ACCEPTED)


def split_pdf(pdf_path, output_dir):
    """Split PDF into individual page images."""
    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(str(pdf_path), dpi=300)
        paths = []
        for i, page in enumerate(pages):
            out = output_dir / f"page_{i+1:04d}.png"
            page.save(str(out), 'PNG')
            paths.append(out)
        return paths
    except Exception:
        return [pdf_path]