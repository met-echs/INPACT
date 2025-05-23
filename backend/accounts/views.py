"""
accounts/views.py — Authentication and profile API views.

All views return JSON. JWT tokens are issued on login.
"""
import logging
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser, EmailVerificationToken, PasswordResetToken
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    EmailVerifySerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    UserWithProfileSerializer,
    UserMinimalSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_tokens_for_user(user: CustomUser) -> dict:
    """Return a dict with refresh and access JWT tokens for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def _send_verification_email(user: CustomUser, request: Request) -> None:
    """Create an email verification token and send it to the user."""
    token = EmailVerificationToken.objects.create(user=user)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
    send_mail(
        subject="Verify Your Email — INPACT",
        message='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=f"""
<html>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
  <div style="max-width:600px; margin:auto; background:#fff; padding:30px;
              border-radius:12px; box-shadow:0 2px 12px rgba(0,0,0,0.1);">
    <h2 style="color:#333;">Hello {user.first_name or user.email},</h2>
    <p style="color:#555;">Thank you for registering with INPACT. Please verify your email address by clicking the button below.</p>
    <a href="{verify_url}"
       style="display:inline-block; margin-top:20px; padding:14px 28px;
              background:#4F46E5; color:#fff; text-decoration:none; border-radius:8px; font-weight:bold;">
      Verify Email Address
    </a>
    <p style="color:#999; margin-top:20px; font-size:13px;">
      This link expires in 24 hours. If you did not create an account, you can safely ignore this email.
    </p>
  </div>
</body>
</html>
""",
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class RegisterView(APIView):
    """
    POST /api/auth/register/

    Register a new student account. Sends email verification link.
    Returns JWT tokens immediately so the student can access the app
    while awaiting email verification.
    """
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email (non-blocking; failures are logged not raised)
        try:
            _send_verification_email(user, request)
        except Exception as exc:
            logger.error("Failed to send verification email to %s: %s", user.email, exc)

        tokens = _get_tokens_for_user(user)
        logger.info("New student registered: %s", user.email)

        return Response(
            {
                "message": "Registration successful. Please check your email to verify your account.",
                "user": UserMinimalSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginView(APIView):
    """
    POST /api/auth/login/

    Authenticate with email + password. Returns JWT access + refresh tokens.
    """
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = _get_tokens_for_user(user)

        logger.info("Student logged in: %s", user.email)

        return Response(
            {
                "user": UserMinimalSerializer(user).data,
                "tokens": tokens,
            },
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Token Refresh (delegated to simplejwt — no custom view needed)
# ---------------------------------------------------------------------------
# Use: POST /api/auth/token/refresh/  with {"refresh": "<token>"}
# Handled by rest_framework_simplejwt.views.TokenRefreshView in urls.py


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------

class VerifyEmailView(APIView):
    """
    GET /api/auth/verify-email/?token=<uuid>

    Marks the user's email as verified and invalidates the token.
    """
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        serializer = EmailVerifySerializer(data={'token': request.query_params.get('token')})
        serializer.is_valid(raise_exception=True)
        token_obj = serializer.validated_data['token']

        user = token_obj.user
        user.is_email_verified = True
        user.save(update_fields=['is_email_verified'])

        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])

        logger.info("Email verified for: %s", user.email)

        return Response(
            {"message": "Email verified successfully. You can now log in."},
            status=status.HTTP_200_OK,
        )


class ResendVerificationView(APIView):
    """
    POST /api/auth/resend-verification/

    Resend a verification email to the currently authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user = request.user
        if user.is_email_verified:
            return Response(
                {"message": "Your email is already verified."},
                status=status.HTTP_200_OK,
            )
        try:
            _send_verification_email(user, request)
        except Exception as exc:
            logger.error("Failed to resend verification email to %s: %s", user.email, exc)
            return Response(
                {"error": "Failed to send verification email. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {"message": "Verification email resent. Please check your inbox."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------

class PasswordResetRequestView(APIView):
    """
    POST /api/auth/password-reset/

    Send a password reset link to the given email.
    Always returns 200 to prevent email enumeration.
    """
    permission_classes = [AllowAny]
    throttle_scope = 'auth'

    def post(self, request: Request) -> Response:
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email'].lower()

        try:
            user = CustomUser.objects.get(email=email)
            token = PasswordResetToken.objects.create(user=user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
            send_mail(
                subject="Reset Your Password — INPACT",
                message='',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=f"""
<html>
<body style="font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px;">
  <div style="max-width:600px; margin:auto; background:#fff; padding:30px;
              border-radius:12px; box-shadow:0 2px 12px rgba(0,0,0,0.1);">
    <h2 style="color:#333;">Password Reset Request</h2>
    <p style="color:#555;">We received a request to reset the password for your INPACT account.</p>
    <a href="{reset_url}"
       style="display:inline-block; margin-top:20px; padding:14px 28px;
              background:#EF4444; color:#fff; text-decoration:none; border-radius:8px; font-weight:bold;">
      Reset My Password
    </a>
    <p style="color:#999; margin-top:20px; font-size:13px;">
      This link expires in 1 hour. If you did not request a password reset, please ignore this email.
    </p>
  </div>
</body>
</html>
""",
            )
            logger.info("Password reset email sent to: %s", email)
        except CustomUser.DoesNotExist:
            # Intentionally silent — do not reveal whether email exists
            pass
        except Exception as exc:
            logger.error("Failed to send password reset email to %s: %s", email, exc)

        return Response(
            {"message": "If an account with that email exists, a reset link has been sent."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """
    POST /api/auth/password-reset/confirm/

    Validate the reset token and set a new password.
    """
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token_obj = serializer.validated_data['token_obj']
        user = token_obj.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])

        logger.info("Password reset completed for: %s", user.email)

        return Response(
            {"message": "Password reset successfully. You can now log in with your new password."},
            status=status.HTTP_200_OK,
        )


# ---------------------------------------------------------------------------
# Student Profile
# ---------------------------------------------------------------------------

class StudentProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/profile/   — Retrieve the authenticated student's profile.
    PUT  /api/auth/profile/   — Full update.
    PATCH /api/auth/profile/  — Partial update.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserWithProfileSerializer

    def get_object(self) -> CustomUser:
        return self.request.user

    def update(self, request: Request, *args, **kwargs) -> Response:
        kwargs['partial'] = True  # Always allow partial updates
        return super().update(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Logout (JWT token blacklist)
# ---------------------------------------------------------------------------

class LogoutView(APIView):
    """
    POST /api/auth/logout/

    Blacklist the refresh token to complete logout.
    Requires djangorestframework-simplejwt with token blacklisting enabled.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("Student logged out: %s", request.user.email)
            return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)
        except Exception as exc:
            logger.warning("Logout failed for %s: %s", request.user.email, exc)
            return Response({"error": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)
