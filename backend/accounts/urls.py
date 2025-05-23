"""
accounts/urls.py — URL patterns for authentication and profile APIs.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    VerifyEmailView,
    ResendVerificationView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    StudentProfileView,
    LogoutView,
)

app_name = 'accounts'

urlpatterns = [
    # ── Authentication ───────────────────────────────────────────────────────
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # ── Email Verification ───────────────────────────────────────────────────
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='resend-verification'),

    # ── Password Reset ───────────────────────────────────────────────────────
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # ── Student Profile ──────────────────────────────────────────────────────
    path('profile/', StudentProfileView.as_view(), name='profile'),
]
