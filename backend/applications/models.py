"""
applications/models.py — Application tracking and 13-stage recruitment workflow model.
"""
from django.db import models
from django.conf import settings
from internships.models import Internship


class ApplicationStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    SUBMITTED = 'submitted', 'Submitted'
    SCREENING = 'screening', 'AI Screening In Progress'
    SHORTLISTED = 'shortlisted', 'Shortlisted (Passed Screening)'
    REJECTED_SCREENING = 'rejected_screening', 'Rejected (Failed Screening)'
    INTERVIEW_SCHEDULED = 'interview_scheduled', 'Interview Scheduled'
    INTERVIEW_COMPLETED = 'interview_completed', 'Interview Completed'
    TECHNICAL_EVAL = 'technical_eval', 'In Technical Evaluation'
    HR_EVAL = 'hr_eval', 'In HR Evaluation'
    OFFERED = 'offered', 'Offer Extended'
    ACCEPTED = 'accepted', 'Offer Accepted'
    DECLINED = 'declined', 'Offer Declined'
    REJECTED = 'rejected', 'Rejected'


class Application(models.Model):
    """
    Tracks a student's application for an internship position through
    the complete 13-stage recruitment lifecycle.
    """
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Student Applicant',
    )
    internship = models.ForeignKey(
        Internship,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Internship Position',
    )
    status = models.CharField(
        max_length=30,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.SUBMITTED,
        db_index=True,
    )

    # ── Uploaded Documents for this application ──────────────────────────────
    resume = models.FileField(
        upload_to='applications/resumes/',
        verbose_name='Application Resume (PDF)',
    )
    cover_letter = models.TextField(blank=True)

    # ── Scores & Evaluation Metrics ──────────────────────────────────────────
    resume_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True, blank=True,
        help_text='AI screening score out of 100',
    )
    interview_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True, blank=True,
        help_text='AI interview score out of 100',
    )
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True, blank=True,
        help_text='Weighted combined score out of 100',
    )

    # ── Recruiter / AI Feedback ──────────────────────────────────────────────
    screening_feedback = models.TextField(blank=True, help_text='AI resume feedback')
    interviewer_feedback = models.TextField(blank=True, help_text='AI or human interviewer notes')
    admin_notes = models.TextField(blank=True, help_text='Internal admin / recruiter notes')

    # ── Timestamps ───────────────────────────────────────────────────────────
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
        ordering = ['-submitted_at']
        unique_together = ('applicant', 'internship')  # 1 application per student per internship
        indexes = [
            models.Index(fields=['applicant', 'status']),
            models.Index(fields=['internship', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['overall_score']),
        ]

    def __str__(self) -> str:
        return f"{self.applicant.email} → {self.internship.title} [{self.get_status_display()}]"


class ApplicationStatusHistory(models.Model):
    """
    Audit log tracking every status transition of an application.
    """
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='status_history',
    )
    from_status = models.CharField(max_length=30, choices=ApplicationStatus.choices)
    to_status = models.CharField(max_length=30, choices=ApplicationStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    reason = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Status History Log'
        ordering = ['-changed_at']

    def __str__(self) -> str:
        return f"App #{self.application_id}: {self.from_status} → {self.to_status}"
