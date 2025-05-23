from django.db import models
from django.contrib.auth.hashers import make_password, check_password as _check_password


class Candidate(models.Model):
    """
    Represents a job applicant who has submitted their resume.

    Passwords are hashed using Django's built-in PBKDF2 hasher — never stored
    as plaintext. Use set_password() to assign and check_password() to verify.
    """
    candidate_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Full Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    password = models.CharField(max_length=255, verbose_name="Password")
    resume_path = models.FileField(upload_to='resumes/', null=True, blank=True)
    resume_score = models.IntegerField(
        null=True, blank=True,
        verbose_name="Resume Score",
        help_text="LLM-generated resume score (0-100)",
    )
    overall_score = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        indexes = [
            models.Index(fields=['email']),
        ]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}>"

    def set_password(self, raw_password: str) -> None:
        """Hash and store the given raw password."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Return True if raw_password matches the stored hash."""
        return _check_password(raw_password, self.password)

    def save(self, *args, **kwargs) -> None:
        """
        Auto-hash the password if it looks like plaintext.
        Django hashed passwords always start with 'pbkdf2_', 'bcrypt', etc.
        """
        if self.password and not self.password.startswith(('pbkdf2_', 'bcrypt', 'argon2', '!')):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
