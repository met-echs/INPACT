"""
accounts app — Student authentication and profile management.

This app provides:
  - CustomUser: AbstractUser-based student account (replaces the legacy Candidate model over time)
  - StudentProfile: Extended profile fields (academic, skills, links, preferences)
  - JWT authentication via djangorestframework-simplejwt
  - Email verification token model
  - Password reset token model
"""
default_app_config = 'accounts.apps.AccountsConfig'
