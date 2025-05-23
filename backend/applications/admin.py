import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import Application, ApplicationStatusHistory, ApplicationStatus


@admin.action(description="Export selected applications to CSV")
def export_applications_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="selected_applications.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Applicant Email', 'Internship', 'Status', 'Resume Score', 'Interview Score', 'Overall Score', 'Submitted Date'])
    for app in queryset.select_related('applicant', 'internship'):
        writer.writerow([
            app.id, app.applicant.email, app.internship.title,
            app.get_status_display(), app.resume_score, app.interview_score, app.overall_score,
            app.submitted_at.strftime('%Y-%m-%d'),
        ])
    return response


@admin.action(description="Mark selected applications as Shortlisted")
def mark_as_shortlisted(modeladmin, request, queryset):
    updated = queryset.update(status=ApplicationStatus.SHORTLISTED)
    modeladmin.message_user(request, f"{updated} application(s) marked as Shortlisted.")


@admin.action(description="Mark selected applications as Rejected")
def mark_as_rejected(modeladmin, request, queryset):
    updated = queryset.update(status=ApplicationStatus.REJECTED)
    modeladmin.message_user(request, f"{updated} application(s) marked as Rejected.")


class ApplicationStatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_by', 'reason', 'changed_at')
    can_delete = False


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    """Admin interface for Applications with status workflow controls."""

    list_display = (
        'id', 'applicant', 'internship', 'status',
        'resume_score', 'interview_score', 'overall_score', 'submitted_at',
    )
    list_filter = ('status', 'submitted_at')
    search_fields = ('applicant__email', 'applicant__first_name', 'internship__title')
    ordering = ('-submitted_at',)
    readonly_fields = ('submitted_at', 'updated_at')
    inlines = [ApplicationStatusHistoryInline]
    actions = [export_applications_csv, mark_as_shortlisted, mark_as_rejected]


    fieldsets = (
        ('Application Info', {
            'fields': ('applicant', 'internship', 'status'),
        }),
        ('Documents', {
            'fields': ('resume', 'cover_letter'),
        }),
        ('Scores & Feedback', {
            'fields': (
                'resume_score', 'interview_score', 'overall_score',
                'screening_feedback', 'interviewer_feedback', 'admin_notes',
            ),
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
        }),
    )


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'from_status', 'to_status', 'changed_by', 'changed_at')
    list_filter = ('to_status', 'changed_at')
    search_fields = ('application__applicant__email', 'reason')
    readonly_fields = ('application', 'from_status', 'to_status', 'changed_by', 'reason', 'changed_at')
