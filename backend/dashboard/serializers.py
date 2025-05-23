"""
dashboard/serializers.py — DRF Serializers for EvaluationCriteria, Question, and Admin.
"""
from rest_framework import serializers
from .models import EvaluationCriteria, Question, Admin


class EvaluationCriteriaSerializer(serializers.ModelSerializer):
    """Serializer for EvaluationCriteria model."""

    class Meta:
        model = EvaluationCriteria
        fields = ('id', 'job_role', 'min_years_experience', 'min_projects', 'certifications_required')


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for Question model."""

    class Meta:
        model = Question
        fields = ('id', 'question_number', 'question', 'specific_area', 'keywords')


class AdminSerializer(serializers.ModelSerializer):
    """Serializer for custom Admin model."""

    class Meta:
        model = Admin
        fields = ('id', 'username')
        read_only_fields = ('id',)
