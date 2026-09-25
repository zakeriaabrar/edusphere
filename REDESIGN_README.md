# EduSphere — Full UI Redesign

This version redesigns the complete EduSphere presentation layer while preserving the existing Django application, database, models, authentication, Google OAuth integration, admin, CRUD, Profile, Courses, Results, Attendance, Schedule, Reports, Analytics, Notifications and Settings routes.

## Design direction
- University academic portal + modern SaaS + LMS
- One shared spacing, typography, color, card, form, table and responsive system
- Desktop sidebar with mobile drawer
- Clean responsive tables and mobile layouts
- No fabricated academic data
- Existing database is preserved

## Run
```bash
python -m pip install -r requirements.txt
python manage.py check
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## v22 Role-Based Student Portal
- The Django superuser is the system administrator and retains full control over students, courses, reports, analytics, academic records, and official profile data.
- New student accounts are routed to a first-login onboarding form when no linked Student record exists.
- Students can submit their personal and academic identity information once; GPA, attendance, status, courses, results, and other official records remain administrator-controlled.
- Students receive a privacy-safe portal containing only their own profile, current courses, results, attendance, schedule, notifications, settings, and account information.
- Student directory, global reports, analytics, academic overview, and all create/update/delete management actions are administrator-only.
- Student profile editing and profile deletion are administrator-only after submission.
- Course detail access for students is limited to courses matching their registered department and semester.
