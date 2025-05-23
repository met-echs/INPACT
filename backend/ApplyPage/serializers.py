"""
ApplyPage/serializers.py — DRF Serializers for Candidate and Resume Upload.
"""
from rest_framework import serializers
from .models import Candidate


class CandidateSerializer(serializers.ModelSerializer):
    """Serializer for Candidate model."""

    class Meta:
        model = Candidate
        fields = ('candidate_id', 'name', 'email', 'resume_score', 'overall_score', 'resume_path', 'created_at')
        read_only_fields = ('candidate_id', 'resume_score', 'overall_score', 'created_at')


class ResumeUploadSerializer(serializers.Serializer):
    """Serializer for candidate resume upload API."""
    name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    file = serializers.FileField(required=True)

    def validate_file(self, value):
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are accepted.")
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size must not exceed 5 MB.")
        return value
