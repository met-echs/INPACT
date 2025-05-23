"""
notifications/models.py — In-app Notification and Interview Schedule models.
"""
from django.db import models
from django.conf import settings
from applications.models import Application


class NotificationType(models.TextChoices):
    INFO = 'info', 'Information'
    APPLICATION_UPDATE = 'app_update', 'Application Status Update'
    INTERVIEW_SCHEDULED = 'interview_scheduled', 'Interview Scheduled'
    OFFER = 'offer', 'Job Offer'
    SYSTEM = 'system', 'System Alert'


class Notification(models.Model):
    """
    In-app notification for students and recruiters.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30,
        choices=NotificationType.choices,
        default=NotificationType.INFO,
    )
    is_read = models.BooleanField(default=False, db_index=True)
    link = models.CharField(max_length=255, blank=True, help_text='Optional relative frontend URL to open')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.title} [{'Read' if self.is_read else 'Unread'}]"


class ScheduleStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Student Confirmation'
    ACCEPTED = 'accepted', 'Accepted by Student'
    DECLINED = 'declined', 'Declined by Student'
    CANCELLED = 'cancelled', 'Cancelled by Recruiter'
    COMPLETED = 'completed', 'Completed'


class InterviewSchedule(models.Model):
    """
    Schedule entry for an interview session attached to an application.
    """
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='schedules',
    )
    title = models.CharField(max_length=255, default='Technical & Behavioral Interview')
    scheduled_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=45)
    meeting_link = models.URLField(blank=True, help_text='Video call or platform link')
    instructions = models.TextField(blank=True, help_text='Pre-interview preparation guidelines')
    status = models.CharField(
        max_length=20,
        choices=ScheduleStatus.choices,
        default=ScheduleStatus.PENDING,
    )
    student_notes = models.TextField(blank=True, help_text='Student decline reason or notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Interview Schedule'
        ordering = ['scheduled_time']

    def __str__(self) -> str:
        return f"Schedule for App #{self.application_id} at {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"
