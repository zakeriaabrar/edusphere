from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from students import views as student_views


urlpatterns = [

    path(
        'admin/',
        admin.site.urls
    ),

    path(
        'accounts/logout/',
        student_views.portal_logout,
        name='portal_logout',
    ),

    path(
        'accounts/',
        include('allauth.urls')
    ),

    path(
        '',
        include('students.urls')
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
