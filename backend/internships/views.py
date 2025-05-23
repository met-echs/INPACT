"""
internships/views.py — API views for Internship listings.
"""
from rest_framework import viewsets, permissions, filters
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from .models import Internship, InternshipStatus
from .serializers import InternshipSerializer, InternshipListSerializer


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read access to anyone, write access to admin users only."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff


class InternshipViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, creating, and updating internships.

    GET /api/internships/ — List active internships (supports search & ordering)
    GET /api/internships/{id}/ — Retrieve internship details
    POST /api/internships/ — Create new internship (Admin only)
    PUT/PATCH /api/internships/{id}/ — Update internship (Admin only)
    DELETE /api/internships/{id}/ — Delete internship (Admin only)
    """
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'company_name', 'location', 'skills_required', 'description']
    ordering_fields = ['created_at', 'application_deadline', 'stipend']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Internship.objects.all()
        # Non-staff users only see ACTIVE internships
        if not (self.request.user and self.request.user.is_staff):
            queryset = queryset.filter(
                status=InternshipStatus.ACTIVE,
                application_deadline__gte=timezone.now(),
            )
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return InternshipListSerializer
        return InternshipSerializer
