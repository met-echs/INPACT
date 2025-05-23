from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # ── REST APIs ────────────────────────────────────────────────────────────
    path('api/auth/', include('accounts.urls', namespace='accounts')),
    path('api/internships/', include('internships.urls', namespace='internships')),
    path('api/applications/', include('applications.urls', namespace='applications')),
    path('api/', include('notifications.urls', namespace='notifications')),
    # ── Legacy template views (preserved) ───────────────────────────────────
    path('apply/', include('ApplyPage.urls')),
    path('interview/', include('Interview.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('', views.home, name='home'),
    path('contact/', views.contact_form, name='contact'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
