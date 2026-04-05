from django.urls import path
from . import views

urlpatterns = [
    path('',           views.exam_list,   name='exam_list'),
    path('<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('modules/',   views.module_list, name='module_list'),
]