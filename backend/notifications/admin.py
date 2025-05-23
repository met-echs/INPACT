from django.contrib import admin
from .models import Notification, InterviewSchedule


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'message')
    ordering = ('-created_at',)


@admin.register(InterviewSchedule)
class InterviewScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'title', 'scheduled_time', 'duration_minutes', 'status', 'created_at')
    list_filter = ('status', 'scheduled_time')
    search_fields = ('application__applicant__email', 'application__internship__title', 'title')
    ordering = ('scheduled_time',)
