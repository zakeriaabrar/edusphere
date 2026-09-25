from django.contrib.auth.models import User
from django.db import models


class Student(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('On Leave', 'On Leave'),
        ('Graduated', 'Graduated'),
    ]

    student_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    address = models.TextField()
    department = models.CharField(max_length=100)
    program = models.CharField(max_length=100)
    semester = models.CharField(max_length=30)
    enrollment_year = models.PositiveIntegerField()
    gpa = models.DecimalField(max_digits=3, decimal_places=2)
    attendance = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    profile_photo = models.FileField(upload_to='profile_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"


class UserSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    institution_name = models.CharField(max_length=150, default='EduSphere University')
    academic_year = models.CharField(max_length=20, default='2026')
    default_semester = models.CharField(max_length=50, default='8th Semester')
    recent_students_count = models.PositiveIntegerField(default=5)
    notifications_enabled = models.BooleanField(default=True)
    academic_alerts = models.BooleanField(default=True)
    attendance_alerts = models.BooleanField(default=True)
    dark_mode = models.BooleanField(default=False)

    def __str__(self):
        return f"Settings - {self.user.username}"


class Course(models.Model):
    """Restored from the project's original Course migration (0002)."""

    course_code = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=100)
    credit = models.PositiveIntegerField(default=3)
    department = models.CharField(max_length=100)
    semester = models.CharField(max_length=30)
    teacher_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"
