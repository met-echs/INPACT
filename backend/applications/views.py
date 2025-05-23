"""
applications/views.py — API views for Application tracking.
"""
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction

from .models import Application, ApplicationStatus, ApplicationStatusHistory
from .serializers import (
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationStatusUpdateSerializer,
    ApplicationStatusHistorySerializer,
)


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for student application lifecycle.

    GET /api/applications/ — List applications (Students: own only; Admins: all)
    POST /api/applications/ — Submit new application
    GET /api/applications/{id}/ — Retrieve application detail & history
    POST /api/applications/{id}/update_status/ — Admin status transition
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['internship__title', 'applicant__email', 'applicant__first_name', 'applicant__last_name']
    ordering_fields = ['submitted_at', 'overall_score', 'resume_score', 'interview_score']
    ordering = ['-submitted_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Application.objects.select_related('applicant', 'internship').prefetch_related('status_history')

        # Students can only view their own applications
        if not user.is_staff:
            queryset = queryset.filter(applicant=user)
        else:
            # Admins can filter by internship ID or status
            internship_id = self.request.query_params.get('internship')
            app_status = self.request.query_params.get('status')
            if internship_id:
                queryset = queryset.filter(internship_id=internship_id)
            if app_status:
                queryset = queryset.filter(status=app_status)

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ApplicationCreateSerializer
        return ApplicationSerializer

    def perform_create(self, serializer):
        application = serializer.save(
            applicant=self.request.user,
            status=ApplicationStatus.SUBMITTED,
        )
        # Log initial status history
        ApplicationStatusHistory.objects.create(
            application=application,
            from_status=ApplicationStatus.DRAFT,
            to_status=ApplicationStatus.SUBMITTED,
            changed_by=self.request.user,
            reason='Application submitted by student.',
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def update_status(self, request, pk=None):
        """
        POST /api/applications/{id}/update_status/
        Admin endpoint to advance or update an application's workflow status.
        """
        application = self.get_object()
        serializer = ApplicationStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        reason = serializer.validated_data.get('reason', '')
        admin_notes = serializer.validated_data.get('admin_notes', '')

        old_status = application.status

        if old_status == new_status:
            return Response(
                {"message": f"Application is already in status '{new_status}'."},
                status=status.HTTP_200_OK,
            )

        with transaction.atomic():
            application.status = new_status
            if admin_notes:
                application.admin_notes = admin_notes
            application.save()

            ApplicationStatusHistory.objects.create(
                application=application,
                from_status=old_status,
                to_status=new_status,
                changed_by=request.user,
                reason=reason or f"Status changed by recruiter ({request.user.email}).",
            )

        return Response(
            {
                "message": f"Status updated from '{old_status}' to '{new_status}'.",
                "application": ApplicationSerializer(application).data,
            },
            status=status.HTTP_200_OK,
        )
