from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, StudentProfile, EmailVerificationToken, PasswordResetToken


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for student user accounts."""

    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'is_email_verified', 'is_active', 'date_joined')
    list_filter = ('is_email_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    # Override fieldsets to include our custom fields
    fieldsets = UserAdmin.fieldsets + (
        ('INPACT', {
            'fields': ('is_email_verified',),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('INPACT', {
            'fields': ('email', 'first_name', 'last_name', 'is_email_verified'),
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin interface for student profiles."""

    list_display = ('user', 'college', 'department', 'cgpa', 'current_year', 'updated_at')
    list_filter = ('current_year', 'department', 'availability')
    search_fields = ('user__email', 'user__first_name', 'college', 'department')
    readonly_fields = ('created_at', 'updated_at', 'resume_uploaded_at')
    ordering = ('-updated_at',)

    fieldsets = (
        ('User', {'fields': ('user',)}),
        ('Personal', {'fields': ('gender', 'date_of_birth', 'phone', 'profile_photo')}),
        ('Address', {'fields': ('address', 'district', 'state', 'country')}),
        ('Online Presence', {'fields': ('linkedin', 'github', 'portfolio')}),
        ('Academic', {'fields': (
            'college', 'university', 'department',
            'current_year', 'semester', 'cgpa', 'graduation_year',
        )}),
        ('Skills', {'fields': (
            'skills', 'programming_languages', 'frameworks', 'tools',
            'certifications', 'achievements', 'languages_known',
        )}),
        ('Preferences', {'fields': ('preferred_domain', 'availability')}),
        ('Resume', {'fields': ('resume', 'resume_uploaded_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used',)
    search_fields = ('user__email',)
    readonly_fields = ('token', 'created_at', 'expires_at')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used')
    list_filter = ('is_used',)
    search_fields = ('user__email',)
    readonly_fields = ('token', 'created_at', 'expires_at')
