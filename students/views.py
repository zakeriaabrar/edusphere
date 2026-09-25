from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.contrib.auth import logout
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

from .forms import CourseForm, ProfileForm, StudentForm, StudentOnboardingForm, UserSettingsForm
from .models import Course, Student, UserSettings


@login_required
def portal_logout(request):
    """Sign out immediately and return to the EduSphere sign-in page."""
    logout(request)
    return redirect('account_login')


def _is_admin(request):
    return request.user.is_authenticated and request.user.is_superuser


def _admin_only(request):
    if not _is_admin(request):
        return HttpResponseForbidden('Administrator access is required for this area.')
    return None


def _student_only(request):
    """Allow administrators or students with a completed profile."""
    if _is_admin(request):
        return None
    if not _current_student(request):
        return redirect('student_onboarding')
    return None


def _current_student(request):
    if not request.user.is_authenticated:
        return None
    return Student.objects.filter(email__iexact=request.user.email).first()


def _grade_label(gpa):
    if gpa is None:
        return 'No result'
    value = float(gpa)
    if value >= 3.75:
        return 'Excellent'
    if value >= 3.00:
        return 'Good'
    if value >= 2.00:
        return 'Satisfactory'
    return 'Needs attention'


@login_required
def student_onboarding(request):
    if _is_admin(request):
        return redirect('dashboard')
    existing = _current_student(request)
    if existing:
        return redirect('dashboard')
    form = StudentOnboardingForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        student = form.save(commit=False)
        student.email = request.user.email.strip().lower()
        student.gpa = 0
        student.attendance = 0
        student.status = 'Active'
        student.save()
        messages.success(request, 'Your information was submitted. Academic records are controlled by the administrator.')
        return redirect('dashboard')
    return render(request, 'students/student_onboarding.html', {'form': form})


@login_required
def dashboard(request):
    """Render the student-focused academic dashboard using existing database data."""
    current_student = _current_student(request)
    if not _is_admin(request) and not current_student:
        return redirect('student_onboarding')

    current_courses = Course.objects.none()
    current_course_count = 0
    if current_student:
        current_course_queryset = Course.objects.filter(
            department=current_student.department,
            semester=current_student.semester,
        ).order_by('course_code')
        current_course_count = current_course_queryset.count()
        current_courses = current_course_queryset[:5]

    return render(request, 'students/dashboard.html', {
        'current_student': current_student,
        'current_courses': current_courses,
        'current_course_count': current_course_count,
        'can_add_student': _is_admin(request),
        'can_add_course': _is_admin(request),
        'student_grade_label': _grade_label(current_student.gpa) if current_student else None,
    })


@login_required
def student_list(request):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    students = Student.objects.all()
    search = request.GET.get('search', '').strip()
    department = request.GET.get('department', '').strip()
    program = request.GET.get('program', '').strip()
    semester = request.GET.get('semester', '').strip()
    status = request.GET.get('status', '').strip()

    if search:
        students = students.filter(
            Q(full_name__icontains=search)
            | Q(student_id__icontains=search)
            | Q(email__icontains=search)
        )
    if department:
        students = students.filter(department=department)
    if program:
        students = students.filter(program=program)
    if semester:
        students = students.filter(semester=semester)
    if status:
        students = students.filter(status=status)

    students = students.order_by('student_id')
    paginator = Paginator(students, 8)
    page_obj = paginator.get_page(request.GET.get('page'))
    all_students = Student.objects.all()
    semester_options = [f'{n}{"st" if n == 1 else "nd" if n == 2 else "rd" if n == 3 else "th"} Semester' for n in range(1, 9)]

    return render(request, 'students/student_list.html', {
        'students': page_obj,
        'page_obj': page_obj,
        'departments': CourseForm.DEPARTMENT_OPTIONS,
        'programs': CourseForm.PROGRAM_OPTIONS,
        'semesters': semester_options,
        'total_students': all_students.count(),
        'active_students': all_students.filter(status='Active').count(),
        'on_leave_students': all_students.filter(status='On Leave').count(),
        'graduated_students': all_students.filter(status='Graduated').count(),
        'search': search,
        'selected_department': department,
        'selected_program': program,
        'selected_semester': semester,
        'selected_status': status,
    })


@login_required
def student_create(request):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    form = StudentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        student = form.save()
        messages.success(request, f'{student.full_name} was added successfully.')
        return redirect('student_detail', student_id=student.id)
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Add Student', 'mode': 'create'})


@login_required
def student_detail(request, student_id):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'students/student_detail.html', {
        'student': student,
        'performance_label': _grade_label(student.gpa),
    })


@login_required
def student_update(request, student_id):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    student = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{student.full_name} was updated successfully.')
        return redirect('student_detail', student_id=student.id)
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Edit Student', 'mode': 'edit', 'student': student})


@login_required
def student_delete(request, student_id):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f'{name} was removed from the student directory.')
        return redirect('student_list')
    return render(request, 'students/student_delete.html', {'student': student})


@login_required
def profile(request):
    if (_denied := _student_only(request)) is not None:
        return _denied
    student = _current_student(request)
    if not student:
        return render(request, 'students/profile.html', {
            'student': None,
            'performance_label': None,
        })

    user = request.user
    current_courses = Course.objects.filter(
        department=student.department,
        semester=student.semester,
    ).order_by('course_code')[:5]
    current_course_count = Course.objects.filter(
        department=student.department,
        semester=student.semester,
    ).count()
    google_connected = SocialAccount.objects.filter(user=user, provider='google').exists()

    return render(request, 'students/profile.html', {
        'student': student,
        'user_account': user,
        'performance_label': _grade_label(student.gpa),
        'current_courses': current_courses,
        'current_course_count': current_course_count,
        'google_connected': google_connected,
    })


@login_required
def profile_edit(request):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    student = _current_student(request)
    if not student:
        messages.error(request, 'No student profile is linked to this account.')
        return redirect('profile')

    form = ProfileForm(request.POST or None, request.FILES or None, instance=student, user=request.user)
    if request.method == 'POST':
        action = request.POST.get('action', 'save_profile')
        if action == 'remove_photo':
            if student.profile_photo:
                student.profile_photo.delete(save=False)
                student.profile_photo = None
                student.save(update_fields=['profile_photo', 'updated_at'])
                messages.success(request, 'Your profile photo was removed.')
            else:
                messages.info(request, 'There is no profile photo to remove.')
            return redirect('profile_edit')

        if form.is_valid():
            old_email = student.email
            updated_student = form.save(commit=False)
            new_email = updated_student.email.strip().lower()
            if new_email != old_email.lower() and request.user.email.lower() != new_email:
                request.user.email = new_email
                request.user.save(update_fields=['email'])
                EmailAddress.objects.filter(user=request.user).update(email=new_email, verified=False, primary=True)
            updated_student.email = new_email
            updated_student.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')

    return render(request, 'students/profile_edit.html', {
        'student': student,
        'user_account': request.user,
        'form': form,
    })


@login_required
def profile_delete(request):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    student = _current_student(request)
    if not student:
        messages.error(request, 'No student profile is linked to this account.')
        return redirect('profile')

    if request.method == 'POST':
        if request.POST.get('confirm_delete') != 'yes':
            messages.error(request, 'Please confirm that you want to delete your profile.')
            return redirect('profile_delete')

        user = request.user
        photo = student.profile_photo
        with transaction.atomic():
            student.delete()
            user.delete()
        if photo:
            photo.delete(save=False)
        logout(request)
        return redirect('/accounts/login/?deleted=1')

    return render(request, 'students/profile_delete.html', {'student': student})


@login_required
def courses(request):
    if (_denied := _student_only(request)) is not None:
        return _denied
    current_student = _current_student(request)
    courses_qs = Course.objects.all()
    if not _is_admin(request):
        courses_qs = courses_qs.filter(department=current_student.department, semester=current_student.semester)
    search = request.GET.get('search', '').strip()
    department = request.GET.get('department', '').strip()
    program = request.GET.get('program', '').strip()
    semester = request.GET.get('semester', '').strip()

    if search:
        courses_qs = courses_qs.filter(
            Q(course_code__icontains=search)
            | Q(course_name__icontains=search)
            | Q(teacher_name__icontains=search)
        )
    if _is_admin(request) and department:
        courses_qs = courses_qs.filter(department=department)
    if _is_admin(request) and program:
        program_department = {
            'B.Sc. in CSE': 'Computer Science & Engineering',
        }
        # Course currently has no program field; use the department mapped to the selected program.
        if program in program_department:
            courses_qs = courses_qs.filter(department=program_department[program])
    if _is_admin(request) and semester:
        courses_qs = courses_qs.filter(semester=semester)

    paginator = Paginator(courses_qs.order_by('course_code'), 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    department_options = CourseForm.DEPARTMENT_OPTIONS
    program_options = CourseForm.PROGRAM_OPTIONS
    semester_options = [f'{n}{"st" if n == 1 else "nd" if n == 2 else "rd" if n == 3 else "th"} Semester' for n in range(1, 9)]
    visible_course_count = Course.objects.count() if _is_admin(request) else courses_qs.count()
    visible_department_count = len(department_options) if _is_admin(request) else 1

    return render(request, 'students/course_list.html', {
        'courses': page_obj,
        'page_obj': page_obj,
        'department_options': department_options,
        'program_options': program_options,
        'semester_options': semester_options,
        'total_course_count': visible_course_count,
        'department_count': visible_department_count,
        'search': search,
        'selected_department': department,
        'selected_program': program,
        'selected_semester': semester,
    })


@login_required
def course_create(request):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    form = CourseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        course = form.save()
        messages.success(request, f'{course.course_code} was added to the course catalog.')
        return redirect('course_detail', course_id=course.id)
    return render(request, 'students/course_form.html', {'form': form, 'title': 'Add Course'})


@login_required
def course_detail(request, course_id):
    if (_denied := _student_only(request)) is not None:
        return _denied
    if _is_admin(request):
        course = get_object_or_404(Course, id=course_id)
    else:
        student = _current_student(request)
        if not student:
            return redirect('student_onboarding')
        course = get_object_or_404(Course, id=course_id, department=student.department, semester=student.semester)
    enrolled_count = Student.objects.filter(department=course.department, semester=course.semester).count()
    return render(request, 'students/course_detail.html', {'course': course, 'enrolled_count': enrolled_count})


@login_required
def course_update(request, course_id):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    course = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'{course.course_code} was updated successfully.')
        return redirect('course_detail', course_id=course.id)
    return render(request, 'students/course_form.html', {'form': form, 'title': 'Edit Course', 'course': course})


@login_required
def course_delete(request, course_id):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        code = course.course_code
        course.delete()
        messages.success(request, f'{code} was removed from the course catalog.')
        return redirect('courses')
    return render(request, 'students/course_delete.html', {'course': course})


@login_required
def results(request):
    if (_denied := _student_only(request)) is not None:
        return _denied
    current_student = _current_student(request)
    semester = request.GET.get('semester', '').strip()
    semester_options = [f'{n}{"st" if n == 1 else "nd" if n == 2 else "rd" if n == 3 else "th"} Semester' for n in range(1, 9)]
    return render(request, 'students/results.html', {
        'current_student': current_student,
        'semester_options': semester_options,
        'selected_semester': semester,
        'has_result_data': False,
        'average_gpa': round(float((Student.objects.filter(pk=current_student.pk).aggregate(value=Avg('gpa')) if current_student and not _is_admin(request) else Student.objects.aggregate(value=Avg('gpa')))['value'] or 0), 2),
    })


@login_required
def attendance(request):
    if (_denied := _student_only(request)) is not None:
        return _denied
    current_student = _current_student(request)
    students = Student.objects.all().order_by('-attendance', 'full_name') if _is_admin(request) else Student.objects.filter(pk=current_student.pk)
    threshold = 75
    return render(request, 'students/attendance.html', {
        'students': students,
        'current_student': current_student,
        'average_attendance': round(float(students.aggregate(value=Avg('attendance'))['value'] or 0), 1),
        'threshold': threshold,
        'below_threshold_count': students.filter(attendance__lt=threshold).count(),
    })


@login_required
def schedule(request):
    if (_denied := _student_only(request)) is not None:
        return _denied
    return render(request, 'students/schedule.html', {
        'has_schedule_data': False,
        'week_label': 'This week',
    })


@login_required
def academic(request):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    students = Student.objects.all()
    return render(request, 'students/academic.html', {
        'total_students': students.count(),
        'average_gpa': round(float(students.aggregate(value=Avg('gpa'))['value'] or 0), 2),
        'average_attendance': round(float(students.aggregate(value=Avg('attendance'))['value'] or 0), 1),
    })


@login_required
def reports(request):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    students = Student.objects.all()
    department = request.GET.get('department', '').strip()
    program = request.GET.get('program', '').strip()
    semester = request.GET.get('semester', '').strip()
    academic_year = request.GET.get('academic_year', '').strip()

    filtered = students
    if department:
        filtered = filtered.filter(department=department)
    if program:
        filtered = filtered.filter(program=program)
    if semester:
        filtered = filtered.filter(semester=semester)
    if academic_year:
        filtered = filtered.filter(enrollment_year=academic_year)

    aggregate = filtered.aggregate(avg_gpa=Avg('gpa'), avg_attendance=Avg('attendance'))
    return render(request, 'students/reports.html', {
        'total_students': filtered.count(),
        'active_students': filtered.filter(status='Active').count(),
        'inactive_students': filtered.filter(status='Inactive').count(),
        'on_leave_students': filtered.filter(status='On Leave').count(),
        'graduated_students': filtered.filter(status='Graduated').count(),
        'average_gpa': round(float(aggregate['avg_gpa'] or 0), 2),
        'average_attendance': round(float(aggregate['avg_attendance'] or 0), 1),
        'department_data': filtered.values('department').annotate(total=Count('id')).order_by('-total'),
        'department_options': CourseForm.DEPARTMENT_OPTIONS,
        'program_options': CourseForm.PROGRAM_OPTIONS,
        'semester_options': [f'{n}{"st" if n == 1 else "nd" if n == 2 else "rd" if n == 3 else "th"} Semester' for n in range(1, 9)],
        'academic_year_options': students.values_list('enrollment_year', flat=True).distinct().order_by('-enrollment_year'),
        'selected_department': department,
        'selected_program': program,
        'selected_semester': semester,
        'selected_academic_year': academic_year,
        'has_report_data': filtered.exists(),
    })


@login_required
def analytics(request):
    if (_denied := _admin_only(request)) is not None:
        return _denied
    students = Student.objects.all()
    department_data = list(students.values('department').annotate(total=Count('id')).order_by('-total'))
    total_students = students.count()
    active_courses = Course.objects.count()
    return render(request, 'students/analytics.html', {
        'average_gpa': round(float(students.aggregate(value=Avg('gpa'))['value'] or 0), 2),
        'average_attendance': round(float(students.aggregate(value=Avg('attendance'))['value'] or 0), 1),
        'total_students': total_students,
        'active_courses': active_courses,
        'gpa_bands': [
            students.filter(gpa__lt=2).count(),
            students.filter(gpa__gte=2, gpa__lt=3).count(),
            students.filter(gpa__gte=3, gpa__lt=3.5).count(),
            students.filter(gpa__gte=3.5).count(),
        ],
        'department_data': department_data,
        'students': students.order_by('-gpa')[:8],
        'has_analytics_data': students.exists(),
    })


@login_required
def notifications(request):
    if (_denied := _student_only(request)) is not None:
        return _denied
    current_student = _current_student(request)
    settings = UserSettings.objects.filter(user=request.user).first()
    notices = []

    if current_student and settings and settings.attendance_alerts and current_student.attendance < 75:
        notices.append({
            'type': 'warning',
            'icon': 'clipboard-check',
            'title': 'Attendance needs attention',
            'body': f'Your current recorded attendance is {current_student.attendance}%. Review the attendance page for the current record.',
            'url': '/attendance/',
            'action': 'Review attendance',
        })

    return render(request, 'students/notifications.html', {
        'notices': notices,
        'current_student': current_student,
    })


@login_required
def settings_page(request):
    if (_denied := _student_only(request)) is not None:
        return _denied
    settings, _ = UserSettings.objects.get_or_create(user=request.user)
    form = UserSettingsForm(request.POST or None, instance=settings, is_admin=_is_admin(request))
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Your EduSphere preferences were saved.')
        return redirect('settings')
    return render(request, 'students/settings.html', {'form': form, 'settings': settings})
