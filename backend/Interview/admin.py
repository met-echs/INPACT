from django.contrib import admin
from .models import Interview, Response


class ResponseInline(admin.TabularInline):
    """Show interview responses inline under each Interview record."""
    model = Response
    extra = 0
    readonly_fields = ('response_id', 'question', 'response_text', 'score')
    can_delete = False


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    """Admin interface for Interview sessions."""

    list_display = ('interview_id', 'candidate', 'job_role', 'total_score', 'interview_date')
    list_filter = ('job_role', 'interview_date')
    search_fields = ('candidate__name', 'candidate__email', 'job_role')
    readonly_fields = ('interview_id', 'interview_date')
    ordering = ('-interview_date',)
    inlines = [ResponseInline]


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    """Admin interface for individual interview responses."""

    list_display = ('response_id', 'interview', 'question', 'score')
    list_filter = ('score',)
    search_fields = ('interview__candidate__name', 'response_text')
    readonly_fields = ('response_id',)
