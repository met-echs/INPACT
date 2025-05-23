"""
internships/models.py — Internship posting model.
"""
from django.db import models
from django.utils import timezone


class InternshipStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active / Accepting Applications'
    CLOSED = 'closed', 'Closed'
    ARCHIVED = 'archived', 'Archived'


class InternshipType(models.TextChoices):
    FULL_TIME = 'full_time', 'Full-time'
    PART_TIME = 'part_time', 'Part-time'
    HYBRID = 'hybrid', 'Hybrid'
    REMOTE = 'remote', 'Remote'


class Internship(models.Model):
    """
    Represents an internship position posted in the recruitment system.
    """
    title = models.CharField(max_length=255, verbose_name='Internship Title')
    company_name = models.CharField(max_length=255, default='INPACT Partner')
    location = models.CharField(max_length=255, default='On-site')
    is_remote = models.BooleanField(default=False)
    internship_type = models.CharField(
        max_length=20,
        choices=InternshipType.choices,
        default=InternshipType.FULL_TIME,
    )
    stipend = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g., ₹15,000/month or Unpaid',
    )
    duration_months = models.PositiveSmallIntegerField(
        default=3,
        help_text='Duration in months',
    )
    description = models.TextField(help_text='Detailed job description')
    requirements = models.TextField(blank=True, help_text='Eligibility and requirements')
    responsibilities = models.TextField(blank=True, help_text='Key responsibilities')
    skills_required = models.TextField(
        blank=True,
        help_text='Comma-separated required skills',
    )

    # Screening & eligibility constraints
    min_cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True, blank=True,
        help_text='Minimum CGPA required to apply',
    )
    departments_allowed = models.TextField(
        blank=True,
        help_text='Comma-separated allowed departments (e.g. CSE, ECE, IT). Empty = all allowed.',
    )
    openings = models.PositiveIntegerField(default=1)

    # Workflow & dates
    status = models.CharField(
        max_length=20,
        choices=InternshipStatus.choices,
        default=InternshipStatus.ACTIVE,
        db_index=True,
    )
    application_deadline = models.DateTimeField()
    start_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Internship'
        verbose_name_plural = 'Internships'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['application_deadline']),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.company_name})"

    @property
    def is_accepting_applications(self) -> bool:
        return self.status == InternshipStatus.ACTIVE and timezone.now() <= self.application_deadline

    def get_skills_list(self) -> list[str]:
        return [s.strip() for s in self.skills_required.split(',') if s.strip()]

    def get_departments_list(self) -> list[str]:
        return [d.strip() for d in self.departments_allowed.split(',') if d.strip()]
