from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class Role(models.TextChoices):
    ADMIN   = 'ADMIN',   'Administrator'
    TEACHER = 'TEACHER', 'Teacher'
    STUDENT = 'STUDENT', 'Student'


class UserManager(BaseUserManager):
    def create_user(self, email, password, role, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user  = self.model(email=email, role=role, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra):
        extra.setdefault('role', Role.ADMIN)
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    email           = models.EmailField(unique=True)
    role            = models.CharField(max_length=10, choices=Role.choices)
    first_name      = models.CharField(max_length=100, blank=True)
    last_name       = models.CharField(max_length=100, blank=True)
    is_active       = models.BooleanField(default=True)
    is_staff        = models.BooleanField(default=False)
    created_at      = models.DateTimeField(default=timezone.now)
    staff_id        = models.CharField(max_length=50, blank=True)
    department      = models.CharField(max_length=100, blank=True)
    student_id      = models.CharField(max_length=50, blank=True)
    enrollment_year = models.PositiveSmallIntegerField(null=True, blank=True)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = []
    objects = UserManager()

    def __str__(self):
        return f'{self.email} ({self.role})'

    def check_permission(self, perm_name):
        perms = {
            Role.ADMIN:   ['manage_structure', 'bulk_print', 'upload_scans', 'view_all'],
            Role.TEACHER: ['create_mcqs', 'review_flags', 'override_grade', 'view_module'],
            Role.STUDENT: ['view_own_results'],
        }
        return perm_name in perms.get(self.role, [])