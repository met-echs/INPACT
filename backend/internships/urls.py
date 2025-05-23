"""
internships/urls.py — Router configuration for internship endpoints.
"""
from rest_framework.routers import DefaultRouter
from .views import InternshipViewSet

app_name = 'internships'

router = DefaultRouter()
router.register(r'', InternshipViewSet, basename='internship')

urlpatterns = router.urls
