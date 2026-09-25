from django.contrib import admin

from .models import Course, Student, UserSettings


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'full_name', 'department', 'semester', 'gpa', 'attendance', 'status')
    search_fields = ('student_id', 'full_name', 'email')
    list_filter = ('department', 'semester', 'status')
    ordering = ('student_id',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_name', 'department', 'semester', 'credit', 'teacher_name')
    search_fields = ('course_code', 'course_name', 'teacher_name')
    list_filter = ('department', 'semester')


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution_name', 'academic_year', 'default_semester')
