# models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password as _check_password


class EvaluationCriteria(models.Model):
    """
    Defines the criteria and weights used to evaluate resumes for a given job role.
    Only one instance is used at a time (singleton pattern via .objects.first()).
    """
    job_role = models.CharField(max_length=255)
    min_years_experience = models.IntegerField(default=0)
    min_projects = models.IntegerField(default=0)
    certifications_required = models.CharField(max_length=255, null=True, blank=True)

    # Configurable scoring weightages (must sum to 100)
    weight_experience = models.PositiveIntegerField(default=25, help_text='Weightage % for experience')
    weight_projects = models.PositiveIntegerField(default=25, help_text='Weightage % for projects')
    weight_certifications = models.PositiveIntegerField(default=25, help_text='Weightage % for certifications')
    weight_ats = models.PositiveIntegerField(default=25, help_text='Weightage % for ATS formatting')

    # Passing cutoff threshold
    shortlist_threshold = models.PositiveIntegerField(default=50, help_text='Minimum score (0-100) to shortlist')

    class Meta:
        verbose_name_plural = "Evaluation Criteria"

    def __str__(self) -> str:
        return f"{self.job_role} (Cutoff: {self.shortlist_threshold}%)"


class Question(models.Model):
    """Interview question with associated scoring metadata."""
    question_number = models.IntegerField(unique=True)
    question = models.TextField()
    specific_area = models.CharField(max_length=255)
    keywords = models.TextField(help_text="Comma-separated keywords for scoring")

    class Meta:
        ordering = ['question_number']

    def __str__(self) -> str:
        return f"Q{self.question_number}: {self.question[:60]}"


class Admin(models.Model):
    """
    Custom admin user model (not Django's AbstractUser).

    Passwords are hashed using Django's PBKDF2 hasher via make_password().
    Use check_password() to verify. The save() method only hashes if the
    stored value does not already look like a Django hash — preventing the
    double-hashing bug that occurs when comparing a hash against a hash.
    """
    username = models.EmailField(unique=True, verbose_name="Email Address")
    password = models.CharField(max_length=255, verbose_name="Password")

    def __str__(self) -> str:
        return self.username

    def set_password(self, raw_password: str) -> None:
        """Hash and store the given raw password."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Return True if raw_password matches the stored hash."""
        return _check_password(raw_password, self.password)

    def save(self, *args, **kwargs) -> None:
        """
        Auto-hash the password only if it is still in plaintext.

        Django hashed passwords always start with a known algorithm prefix
        (e.g. 'pbkdf2_sha256$', 'bcrypt$', 'argon2'). If the stored value
        does NOT start with one of those prefixes, it is treated as plaintext
        and hashed before saving — preventing double-hashing on subsequent
        saves.
        """
        _HASH_PREFIXES = ('pbkdf2_', 'bcrypt', 'argon2', '!')
        if self.password and not self.password.startswith(_HASH_PREFIXES):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
