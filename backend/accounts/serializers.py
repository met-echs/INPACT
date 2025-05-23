"""
accounts/serializers.py — DRF serializers for authentication and profiles.
"""
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import CustomUser, StudentProfile, EmailVerificationToken, PasswordResetToken


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for new student registration.

    Validates that:
    - email is unique
    - password meets Django's password validators
    - password and confirm_password match
    """
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'password', 'confirm_password')
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate_email(self, value: str) -> str:
        if CustomUser.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()

    def validate(self, data: dict) -> dict:
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        validate_password(data['password'])
        return data

    def create(self, validated_data: dict) -> CustomUser:
        validated_data.pop('confirm_password')
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_email_verified=False,
        )
        return user


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    """Validates email/password credentials and returns the user object."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data: dict) -> dict:
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")
        data['user'] = user
        return data


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------

class EmailVerifySerializer(serializers.Serializer):
    """Accepts a verification token UUID string."""
    token = serializers.UUIDField(required=True)

    def validate_token(self, value):
        try:
            token_obj = EmailVerificationToken.objects.select_related('user').get(token=value)
        except EmailVerificationToken.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification token.")
        if not token_obj.is_valid:
            raise serializers.ValidationError("This token has already been used or has expired.")
        return token_obj


# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------

class PasswordResetRequestSerializer(serializers.Serializer):
    """Accepts an email to initiate a password reset flow."""
    email = serializers.EmailField(required=True)

    def validate_email(self, value: str) -> str:
        try:
            user = CustomUser.objects.get(email__iexact=value)
        except CustomUser.DoesNotExist:
            # Do not reveal whether the email exists — silently succeed.
            return value
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Accepts a reset token + new password to complete password reset."""
    token = serializers.UUIDField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data: dict) -> dict:
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"new_password": "Passwords do not match."})
        validate_password(data['new_password'])
        try:
            token_obj = PasswordResetToken.objects.select_related('user').get(token=data['token'])
        except PasswordResetToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Invalid or expired reset token."})
        if not token_obj.is_valid:
            raise serializers.ValidationError({"token": "This token has already been used or has expired."})
        data['token_obj'] = token_obj
        return data


# ---------------------------------------------------------------------------
# Student Profile
# ---------------------------------------------------------------------------

class StudentProfileSerializer(serializers.ModelSerializer):
    """Full profile serializer — used for read + update."""

    class Meta:
        model = StudentProfile
        exclude = ('user', 'id')  # user is set from request, id is internal

    def validate_cgpa(self, value):
        if value is not None and not (0 <= value <= 10):
            raise serializers.ValidationError("CGPA must be between 0 and 10.")
        return value

    def validate_resume(self, file):
        if file:
            if not file.name.lower().endswith('.pdf'):
                raise serializers.ValidationError("Resume must be a PDF file.")
            max_size = 5 * 1024 * 1024  # 5 MB
            if file.size > max_size:
                raise serializers.ValidationError("Resume must be smaller than 5 MB.")
        return file


class UserWithProfileSerializer(serializers.ModelSerializer):
    """
    Combined serializer for the student dashboard — user info + profile.
    Read-only fields (email, is_email_verified) cannot be changed here.
    """
    profile = StudentProfileSerializer()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'first_name', 'last_name',
            'is_email_verified', 'date_joined', 'profile',
        )
        read_only_fields = ('id', 'email', 'is_email_verified', 'date_joined')

    def update(self, instance: CustomUser, validated_data: dict) -> CustomUser:
        profile_data = validated_data.pop('profile', {})
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        # Update profile fields
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        return instance


# ---------------------------------------------------------------------------
# Minimal User Serializer (for token responses)
# ---------------------------------------------------------------------------

class UserMinimalSerializer(serializers.ModelSerializer):
    """Lightweight user info returned alongside JWT tokens on login."""

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'first_name', 'last_name', 'is_email_verified')
        read_only_fields = fields
