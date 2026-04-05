from django.db import models
from accounts.models import User


class Module(models.Model):
    code         = models.CharField(max_length=20, unique=True)
    name         = models.CharField(max_length=100)
    credit_hours = models.PositiveSmallIntegerField(default=3)
    teacher      = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'TEACHER'}
    )

    def __str__(self):
        return f'{self.code} - {self.name}'


class Exam(models.Model):
    title        = models.CharField(max_length=200)
    module       = models.ForeignKey(Module, on_delete=models.CASCADE)
    teacher      = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'TEACHER'}
    )
    created_at   = models.DateTimeField(auto_now_add=True)
    is_active    = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.title} - {self.module.code}'


class Question(models.Model):
    ANSWERS = [
        ('A', 'A'), ('B', 'B'),
        ('C', 'C'), ('D', 'D'), ('E', 'E'),
    ]
    exam           = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    order          = models.PositiveSmallIntegerField()
    correct_answer = models.CharField(max_length=1, choices=ANSWERS)
    weight         = models.FloatField(default=1.0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Q{self.order} → {self.correct_answer}'