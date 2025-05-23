"""
notifications/urls.py — Router configuration for notifications and scheduling endpoints.
"""
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, InterviewScheduleViewSet

app_name = 'notifications'

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'schedules', InterviewScheduleViewSet, basename='schedule')

urlpatterns = router.urls
