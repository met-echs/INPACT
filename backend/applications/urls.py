"""
applications/urls.py — Router configuration for application endpoints.
"""
from rest_framework.routers import DefaultRouter
from .views import ApplicationViewSet

app_name = 'applications'

router = DefaultRouter()
router.register(r'', ApplicationViewSet, basename='application')

urlpatterns = router.urls
