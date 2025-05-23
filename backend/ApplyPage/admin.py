from django.contrib import admin
from .models import Candidate


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    """Admin interface for the Candidate model."""

    list_display = ('candidate_id', 'name', 'email', 'resume_score', 'overall_score', 'created_at')
    list_filter = ('resume_score', 'created_at')
    search_fields = ('name', 'email')
    readonly_fields = ('candidate_id', 'created_at', 'resume_score', 'overall_score')
    ordering = ('-created_at',)

    fieldsets = (
        ('Personal Info', {
            'fields': ('candidate_id', 'name', 'email', 'created_at'),
        }),
        ('Resume', {
            'fields': ('resume_path', 'resume_score'),
        }),
        ('Scores', {
            'fields': ('overall_score',),
        }),
        ('Security', {
            'fields': ('password',),
            'classes': ('collapse',),
            'description': 'Password is stored as a PBKDF2 hash. Do not edit directly.',
        }),
    )

    def save_model(self, request, obj, form, change):
        """Ensure password is hashed if updated via admin panel."""
        _HASH_PREFIXES = ('pbkdf2_', 'bcrypt', 'argon2', '!')
        if obj.password and not obj.password.startswith(_HASH_PREFIXES):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)
