"""
notifications/views.py — API views for Notifications and Interview Scheduling.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from .models import Notification, InterviewSchedule, ScheduleStatus
from .serializers import (
    NotificationSerializer,
    InterviewScheduleSerializer,
    ScheduleResponseSerializer,
)
from applications.models import Application, ApplicationStatus, ApplicationStatusHistory


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/notifications/ — List user's notifications
    POST /api/notifications/{id}/mark_read/ — Mark single notification as read
    POST /api/notifications/mark_all_read/ — Mark all notifications as read
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"message": f"{updated} notification(s) marked as read."}, status=status.HTTP_200_OK)


class InterviewScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for scheduling and confirming interviews.

    Admins create interview schedules. Students can view and accept/decline.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = InterviewScheduleSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return InterviewSchedule.objects.select_related('application', 'application__applicant', 'application__internship')
        return InterviewSchedule.objects.filter(application__applicant=user).select_related('application', 'application__internship')

    def perform_create(self, serializer):
        schedule = serializer.save()
        # Update application status to INTERVIEW_SCHEDULED
        app = schedule.application
        old_status = app.status
        app.status = ApplicationStatus.INTERVIEW_SCHEDULED
        app.save(update_fields=['status'])

        ApplicationStatusHistory.objects.create(
            application=app,
            from_status=old_status,
            to_status=ApplicationStatus.INTERVIEW_SCHEDULED,
            changed_by=self.request.user,
            reason=f"Interview scheduled for {schedule.scheduled_time.strftime('%Y-%m-%d %H:%M')}",
        )

        # Send in-app notification to student
        Notification.objects.create(
            user=app.applicant,
            title="Interview Scheduled!",
            message=f"An interview for '{app.internship.title}' has been scheduled for {schedule.scheduled_time.strftime('%Y-%m-%d %H:%M')}.",
            notification_type='interview_scheduled',
            link=f"/applications/{app.id}",
        )

    @action(detail=True, methods=['post'])
    def respond(self, request, pk=None):
        """
        POST /api/schedules/{id}/respond/
        Student accepts or declines an interview invitation.
        """
        schedule = self.get_object()
        serializer = ScheduleResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_action = serializer.validated_data['action']
        notes = serializer.validated_data.get('student_notes', '')

        if user_action == 'accept':
            schedule.status = ScheduleStatus.ACCEPTED
            msg = "Interview schedule accepted successfully."
        else:
            schedule.status = ScheduleStatus.DECLINED
            msg = "Interview schedule declined."

        if notes:
            schedule.student_notes = notes
        schedule.save()

        return Response({"message": msg, "schedule": InterviewScheduleSerializer(schedule).data}, status=status.HTTP_200_OK)
