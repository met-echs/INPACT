from django.contrib import admin
from .models import EvaluationCriteria, Question, Admin as AdminModel


@admin.register(EvaluationCriteria)
class EvaluationCriteriaAdmin(admin.ModelAdmin):
    """Admin interface for evaluation criteria (resume screening config)."""

    list_display = ('job_role', 'min_years_experience', 'min_projects', 'certifications_required')
    search_fields = ('job_role',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Admin interface for interview questions."""

    list_display = ('question_number', 'specific_area', 'question_preview', 'keywords')
    list_filter = ('specific_area',)
    search_fields = ('question', 'specific_area', 'keywords')
    ordering = ('question_number',)

    @admin.display(description='Question Preview')
    def question_preview(self, obj):
        return obj.question[:80] + ('…' if len(obj.question) > 80 else '')


@admin.register(AdminModel)
class AdminModelAdmin(admin.ModelAdmin):
    """Admin interface for custom Admin users."""

    list_display = ('username',)
    search_fields = ('username',)
    readonly_fields = ('password',)

    def save_model(self, request, obj, form, change):
        """Ensure password is hashed if set/updated via admin panel."""
        _HASH_PREFIXES = ('pbkdf2_', 'bcrypt', 'argon2', '!')
        if obj.password and not obj.password.startswith(_HASH_PREFIXES):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)
