"""
applications/serializers.py — DRF Serializers for Application tracking.
"""
from rest_framework import serializers
from .models import Application, ApplicationStatusHistory, ApplicationStatus
from internships.serializers import InternshipListSerializer
from accounts.serializers import UserMinimalSerializer


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    """Audit log history serializer."""
    changed_by_email = serializers.ReadOnlyField(source='changed_by.email')

    class Meta:
        model = ApplicationStatusHistory
        fields = ('id', 'from_status', 'to_status', 'changed_by_email', 'reason', 'changed_at')


class ApplicationSerializer(serializers.ModelSerializer):
    """Detailed serializer for student/admin viewing an application."""
    internship_detail = InternshipListSerializer(source='internship', read_only=True)
    applicant_detail = UserMinimalSerializer(source='applicant', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True)

    class Meta:
        model = Application
        fields = (
            'id', 'applicant', 'applicant_detail', 'internship', 'internship_detail',
            'status', 'status_display', 'resume', 'cover_letter',
            'resume_score', 'interview_score', 'overall_score',
            'screening_feedback', 'interviewer_feedback', 'admin_notes',
            'status_history', 'submitted_at', 'updated_at',
        )
        read_only_fields = (
            'id', 'applicant', 'status', 'resume_score', 'interview_score',
            'overall_score', 'screening_feedback', 'interviewer_feedback',
            'admin_notes', 'submitted_at', 'updated_at',
        )


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for students submitting a new application."""

    class Meta:
        model = Application
        fields = ('internship', 'resume', 'cover_letter')

    def validate_resume(self, file):
        if not file.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Resume must be a PDF file.")
        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Resume size must not exceed 5 MB.")
        return file

    def validate(self, data: dict) -> dict:
        user = self.context['request'].user
        internship = data['internship']

        # Check if active
        if not internship.is_accepting_applications:
            raise serializers.ValidationError("This internship is no longer accepting applications.")

        # Check if duplicate application
        if Application.objects.filter(applicant=user, internship=internship).exists():
            raise serializers.ValidationError("You have already applied for this internship.")

        return data


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    """Serializer for admin updating an application's status."""
    status = serializers.ChoiceField(choices=ApplicationStatus.choices)
    reason = serializers.CharField(required=False, allow_blank=True)
    admin_notes = serializers.CharField(required=False, allow_blank=True)
