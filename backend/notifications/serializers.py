"""
notifications/serializers.py — DRF Serializers for Notifications and Scheduling.
"""
from rest_framework import serializers
from .models import Notification, InterviewSchedule, ScheduleStatus


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'title', 'message', 'notification_type', 'is_read', 'link', 'created_at')
        read_only_fields = ('id', 'title', 'message', 'notification_type', 'link', 'created_at')


class InterviewScheduleSerializer(serializers.ModelSerializer):
    applicant_email = serializers.ReadOnlyField(source='application.applicant.email')
    internship_title = serializers.ReadOnlyField(source='application.internship.title')

    class Meta:
        model = InterviewSchedule
        fields = (
            'id', 'application', 'applicant_email', 'internship_title',
            'title', 'scheduled_time', 'duration_minutes', 'meeting_link',
            'instructions', 'status', 'student_notes', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class ScheduleResponseSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['accept', 'decline'])
    student_notes = serializers.CharField(required=False, allow_blank=True)
