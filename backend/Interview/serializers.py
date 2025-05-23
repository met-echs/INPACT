"""
Interview/serializers.py — DRF Serializers for Interview and Response models.
"""
from rest_framework import serializers
from .models import Interview, Response
from ApplyPage.serializers import CandidateSerializer


class ResponseSerializer(serializers.ModelSerializer):
    """Serializer for individual interview response."""

    class Meta:
        model = Response
        fields = ('response_id', 'interview', 'question', 'response_text', 'score')
        read_only_fields = ('response_id',)


class InterviewSerializer(serializers.ModelSerializer):
    """Serializer for Interview session, including nested responses."""
    responses = ResponseSerializer(many=True, read_only=True)
    candidate_detail = CandidateSerializer(source='candidate', read_only=True)

    class Meta:
        model = Interview
        fields = (
            'interview_id', 'candidate', 'candidate_detail',
            'job_role', 'total_score', 'video_path', 'interview_date',
            'responses',
        )
        read_only_fields = ('interview_id', 'interview_date')
