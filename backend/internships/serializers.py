"""
internships/serializers.py — DRF Serializers for Internship postings.
"""
from rest_framework import serializers
from .models import Internship


class InternshipSerializer(serializers.ModelSerializer):
    """Full serializer for Internship model."""
    is_accepting_applications = serializers.ReadOnlyField()
    skills_list = serializers.ListField(source='get_skills_list', read_only=True)
    departments_list = serializers.ListField(source='get_departments_list', read_only=True)

    class Meta:
        model = Internship
        fields = (
            'id', 'title', 'company_name', 'location', 'is_remote',
            'internship_type', 'stipend', 'duration_months',
            'description', 'requirements', 'responsibilities',
            'skills_required', 'skills_list', 'min_cgpa',
            'departments_allowed', 'departments_list', 'openings',
            'status', 'application_deadline', 'start_date',
            'is_accepting_applications', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class InternshipListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for internship search & listing."""
    is_accepting_applications = serializers.ReadOnlyField()
    skills_list = serializers.ListField(source='get_skills_list', read_only=True)

    class Meta:
        model = Internship
        fields = (
            'id', 'title', 'company_name', 'location', 'is_remote',
            'internship_type', 'stipend', 'duration_months',
            'skills_list', 'min_cgpa', 'openings', 'status',
            'application_deadline', 'is_accepting_applications',
        )
