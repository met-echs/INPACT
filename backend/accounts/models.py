"""
accounts/models.py — Student user and profile models.

Design decisions:
  - CustomUser extends AbstractUser so we get Django's full auth system
    (password hashing, permissions, sessions, admin integration) for free.
  - StudentProfile holds all extended fields to keep the auth model lean.
    It is linked 1-to-1 via OneToOneField so each user has exactly one profile.
  - EmailVerificationToken and PasswordResetToken are simple time-limited
    tokens stored in the DB (no external service required).
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


# ---------------------------------------------------------------------------
# Choices
# ---------------------------------------------------------------------------

class Gender(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'
    OTHER = 'O', 'Other'
    PREFER_NOT = 'N', 'Prefer not to say'


class YearOfStudy(models.TextChoices):
    FIRST = '1', '1st Year'
    SECOND = '2', '2nd Year'
    THIRD = '3', '3rd Year'
    FOURTH = '4', '4th Year'
    FIFTH = '5', '5th Year'
    GRADUATE = 'G', 'Graduate'


class AvailabilityType(models.TextChoices):
    IMMEDIATE = 'immediate', 'Immediately Available'
    ONE_MONTH = '1_month', 'Available in 1 Month'
    TWO_MONTHS = '2_months', 'Available in 2 Months'
    THREE_MONTHS = '3_months', 'Available in 3 Months'
    FLEXIBLE = 'flexible', 'Flexible'


from django.contrib.auth.models import AbstractUser, BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier for authentication.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email.split('@')[0])
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Extended user model for student accounts.

    We override AbstractUser to add email as the primary identifier and
    enforce email uniqueness. Django's built-in fields (password hashing,
    groups, permissions) are inherited without modification.

    USERNAME_FIELD = 'email' means login is done with email, not username.
    """
    objects = CustomUserManager()

    # Make email the login identifier
    email = models.EmailField(unique=True, verbose_name='Email Address')

    # Django requires username — keep it but make it optional / auto-set
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        help_text='Auto-populated from email if not provided.',
    )

    # Email verification
    is_email_verified = models.BooleanField(default=False, verbose_name='Email Verified')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # required by createsuperuser only

    class Meta:
        verbose_name = 'Student User'
        verbose_name_plural = 'Student Users'
        indexes = [
            models.Index(fields=['email']),
        ]

    def __str__(self) -> str:
        full_name = self.get_full_name()
        return full_name if full_name else self.email

    def save(self, *args, **kwargs) -> None:
        """Auto-populate username from email if not provided."""
        if not self.username:
            base = self.email.split('@')[0]
            username = base
            counter = 1
            while CustomUser.objects.filter(username=username).exclude(pk=self.pk).exists():
                username = f"{base}{counter}"
                counter += 1
            self.username = username
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Student Profile
# ---------------------------------------------------------------------------

class StudentProfile(models.Model):
    """
    Extended profile for a student user.

    Separated from CustomUser to keep the auth model lean and to allow
    profile data to be optional / filled in progressively.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User Account',
    )

    # ── Personal Information ─────────────────────────────────────────────────
    gender = models.CharField(
        max_length=1, choices=Gender.choices, blank=True, null=True,
    )
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = models.FileField(
        upload_to='profiles/photos/',
        null=True, blank=True,
        verbose_name='Profile Photo',
        # TODO: Change back to models.ImageField once Pillow is installed.
        # ImageField is a strict superset of FileField (adds image validation).
    )

    # ── Address ──────────────────────────────────────────────────────────────
    address = models.TextField(blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True, default='India')

    # ── Online Presence ──────────────────────────────────────────────────────
    linkedin = models.URLField(blank=True, verbose_name='LinkedIn URL')
    github = models.URLField(blank=True, verbose_name='GitHub URL')
    portfolio = models.URLField(blank=True, verbose_name='Portfolio URL')

    # ── Academic Information ─────────────────────────────────────────────────
    college = models.CharField(max_length=255, blank=True)
    university = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=255, blank=True)
    current_year = models.CharField(
        max_length=1,
        choices=YearOfStudy.choices,
        blank=True,
    )
    semester = models.PositiveSmallIntegerField(null=True, blank=True)
    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True, blank=True,
        help_text='Current CGPA on a 10-point scale.',
    )
    graduation_year = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='Expected or actual graduation year.',
    )

    # ── Skills & Technical Profile ───────────────────────────────────────────
    # Stored as comma-separated text for simplicity; can be migrated to
    # ArrayField (PostgreSQL) or a ManyToMany later.
    skills = models.TextField(
        blank=True,
        help_text='Comma-separated list of skills.',
    )
    programming_languages = models.TextField(
        blank=True,
        help_text='Comma-separated list of programming languages.',
    )
    frameworks = models.TextField(
        blank=True,
        help_text='Comma-separated list of frameworks/libraries.',
    )
    tools = models.TextField(
        blank=True,
        help_text='Comma-separated list of tools/platforms.',
    )
    certifications = models.TextField(
        blank=True,
        help_text='Comma-separated list of certifications.',
    )
    achievements = models.TextField(blank=True)
    languages_known = models.TextField(
        blank=True,
        help_text='Comma-separated list of languages (spoken/written).',
    )

    # ── Internship Preferences ───────────────────────────────────────────────
    preferred_domain = models.CharField(
        max_length=255, blank=True,
        verbose_name='Preferred Internship Domain',
    )
    availability = models.CharField(
        max_length=20,
        choices=AvailabilityType.choices,
        blank=True,
    )

    # ── Resume ───────────────────────────────────────────────────────────────
    resume = models.FileField(
        upload_to='profiles/resumes/',
        null=True, blank=True,
        verbose_name='Current Resume (PDF)',
        help_text='Maximum 5 MB, PDF only.',
    )
    resume_uploaded_at = models.DateTimeField(null=True, blank=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Student Profile'
        verbose_name_plural = 'Student Profiles'
        indexes = [
            models.Index(fields=['college']),
            models.Index(fields=['department']),
            models.Index(fields=['cgpa']),
            models.Index(fields=['graduation_year']),
        ]

    def __str__(self) -> str:
        return f"Profile of {self.user}"

    def get_skills_list(self) -> list[str]:
        """Return skills as a cleaned Python list."""
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def get_programming_languages_list(self) -> list[str]:
        return [s.strip() for s in self.programming_languages.split(',') if s.strip()]


# ---------------------------------------------------------------------------
# Email Verification Token
# ---------------------------------------------------------------------------

def _token_expiry() -> timezone.datetime:
    """Return a datetime 24 hours from now."""
    return timezone.now() + timedelta(hours=24)


class EmailVerificationToken(models.Model):
    """
    One-time token for verifying a student's email address.

    Tokens expire after 24 hours. A new token is created on every
    resend-verification request (old ones can be cleaned up by a management
    command or Celery task).
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_tokens',
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=_token_expiry)
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Email Verification Token'

    def __str__(self) -> str:
        return f"Verification token for {self.user.email}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired


# ---------------------------------------------------------------------------
# Password Reset Token
# ---------------------------------------------------------------------------

class PasswordResetToken(models.Model):
    """
    One-time token for resetting a student's password.
    Expires after 1 hour.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Password Reset Token'

    def save(self, *args, **kwargs):
        if not self.pk:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Reset token for {self.user.email}"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired
