from django.contrib import admin
from .models import Module, Exam, Question


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'credit_hours', 'teacher']
    search_fields = ['code', 'name']


class QuestionInline(admin.TabularInline):
    model  = Question
    extra  = 5


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display  = ['title', 'module', 'teacher', 'created_at', 'is_active']
    list_filter   = ['is_active', 'module']
    search_fields = ['title']
    inlines       = [QuestionInline]