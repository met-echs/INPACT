from django.contrib import admin
from .models import Internship


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    """Admin interface for Internship postings."""

    list_display = (
        'title', 'company_name', 'location', 'internship_type',
        'openings', 'status', 'application_deadline', 'created_at',
    )
    list_filter = ('status', 'internship_type', 'is_remote', 'created_at')
    search_fields = ('title', 'company_name', 'location', 'skills_required')
    ordering = ('-created_at',)

    fieldsets = (
        ('Overview', {
            'fields': ('title', 'company_name', 'location', 'is_remote', 'internship_type'),
        }),
        ('Compensation & Duration', {
            'fields': ('stipend', 'duration_months', 'openings'),
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'responsibilities', 'skills_required'),
        }),
        ('Eligibility Criteria', {
            'fields': ('min_cgpa', 'departments_allowed'),
        }),
        ('Status & Deadlines', {
            'fields': ('status', 'application_deadline', 'start_date'),
        }),
    )
