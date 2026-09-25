from django import forms
from PIL import Image, UnidentifiedImageError

from .models import Course, Student, UserSettings


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'student_id', 'full_name', 'email', 'phone', 'date_of_birth',
            'gender', 'address', 'department', 'program', 'semester',
            'enrollment_year', 'gpa', 'attendance', 'status',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gpa': forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'max': '4'}),
            'attendance': forms.NumberInput(attrs={'min': '0', 'max': '100'}),
            'address': forms.Textarea(attrs={'rows': 4}),
        }

    DEPARTMENT_OPTIONS = ['Computer Science & Engineering']
    PROGRAM_OPTIONS = ['B.Sc. in CSE']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'] = forms.ChoiceField(
            choices=[(value, value) for value in self.DEPARTMENT_OPTIONS],
        )
        self.fields['program'] = forms.ChoiceField(
            choices=[(value, value) for value in self.PROGRAM_OPTIONS],
        )

    def clean_gpa(self):
        gpa = self.cleaned_data['gpa']
        if gpa < 0 or gpa > 4:
            raise forms.ValidationError('GPA must be between 0 and 4.')
        return gpa

    def clean_attendance(self):
        attendance = self.cleaned_data['attendance']
        if attendance < 0 or attendance > 100:
            raise forms.ValidationError('Attendance must be between 0 and 100.')
        return attendance


class StudentOnboardingForm(forms.ModelForm):
    """Student-submitted information. Official academic metrics remain admin-controlled."""
    class Meta:
        model = Student
        fields = [
            'student_id', 'full_name', 'phone', 'date_of_birth', 'gender', 'address',
            'department', 'program', 'semester', 'enrollment_year', 'profile_photo',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 4}),
            'enrollment_year': forms.NumberInput(attrs={'min': '2000', 'max': '2100'}),
        }

    DEPARTMENT_OPTIONS = [
        'Computer Science & Engineering',
    ]
    PROGRAM_OPTIONS = [
        'B.Sc. in CSE',
    ]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['department'] = forms.ChoiceField(
            choices=[('', 'Select department')] + [(v, v) for v in self.DEPARTMENT_OPTIONS]
        )
        self.fields['program'] = forms.ChoiceField(
            choices=[('', 'Select program')] + [(v, v) for v in self.PROGRAM_OPTIONS]
        )
        self.fields['semester'] = forms.ChoiceField(
            choices=[('', 'Select semester')] + [(f'{n}{"st" if n == 1 else "nd" if n == 2 else "rd" if n == 3 else "th"} Semester', f'{n}{"st" if n == 1 else "nd" if n == 2 else "rd" if n == 3 else "th"} Semester') for n in range(1, 9)]
        )

    def clean_student_id(self):
        value = self.cleaned_data['student_id'].strip()
        if Student.objects.filter(student_id=value).exists():
            raise forms.ValidationError('This student ID is already registered. Please contact the administrator if this is your ID.')
        return value


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_code', 'course_name', 'credit', 'department', 'semester', 'teacher_name']
        widgets = {
            'credit': forms.NumberInput(attrs={'min': '1', 'max': '12'}),
        }

    DEPARTMENT_OPTIONS = [
        'Computer Science & Engineering',
    ]

    PROGRAM_OPTIONS = [
        'B.Sc. in CSE',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'] = forms.ChoiceField(
            choices=[('', 'Select department')] + [(value, value) for value in self.DEPARTMENT_OPTIONS],
            widget=forms.Select(),
        )


class UserSettingsForm(forms.ModelForm):
    def __init__(self, *args, is_admin=False, **kwargs):
        super().__init__(*args, **kwargs)
        if not is_admin:
            for field_name in ['institution_name', 'academic_year', 'default_semester', 'recent_students_count']:
                self.fields.pop(field_name, None)

    class Meta:
        model = UserSettings
        fields = [
            'institution_name', 'academic_year', 'default_semester',
            'recent_students_count', 'notifications_enabled',
            'academic_alerts', 'attendance_alerts', 'dark_mode',
        ]


class ProfileForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    class Meta:
        model = Student
        fields = ['full_name', 'email', 'phone', 'date_of_birth', 'gender', 'address', 'profile_photo']
        widgets = {
            'email': forms.EmailInput(),
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        from django.contrib.auth.models import User
        query = User.objects.filter(email__iexact=email)
        if self.user and self.user.pk:
            query = query.exclude(pk=self.user.pk)
        if query.exists():
            raise forms.ValidationError('This email address is already associated with another account.')
        return email

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if not photo:
            return photo
        allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
        allowed_extensions = ('.jpg', '.jpeg', '.png', '.webp')
        if photo.content_type not in allowed_types or not photo.name.lower().endswith(allowed_extensions):
            raise forms.ValidationError('Please upload a valid JPG, PNG, or WebP image.')
        if photo.size > 5 * 1024 * 1024:
            raise forms.ValidationError('Profile photos must be 5 MB or smaller.')
        try:
            image = Image.open(photo)
            image.verify()
        except (UnidentifiedImageError, OSError):
            raise forms.ValidationError('The uploaded file is not a valid image.')
        finally:
            try:
                photo.seek(0)
            except (AttributeError, OSError):
                pass
        return photo
