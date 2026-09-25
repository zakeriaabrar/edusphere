from .models import Student, UserSettings


def portal_context(request):
    current_student = None
    portal_settings = None

    if request.user.is_authenticated:
        current_student = Student.objects.filter(email__iexact=request.user.email).first()
        portal_settings = UserSettings.objects.filter(user=request.user).first()

    return {
        'current_student': current_student,
        'portal_settings': portal_settings,
        'is_portal_admin': bool(request.user.is_authenticated and request.user.is_superuser),
    }
