from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.submission_list,   name='submission_list'),
    path('<int:sub_id>/',           views.submission_detail, name='submission_detail'),
    path('<int:sub_id>/override/',  views.override_grade,    name='override_grade'),
    path('stats/<int:exam_id>/',    views.exam_statistics,   name='exam_statistics'),
    path('upload/<int:exam_id>/',   views.upload_scans,      name='upload_scans'),
]