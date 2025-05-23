"""
applications/tests.py — Unit tests for Application and 13-stage status workflow.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from internships.models import Internship, InternshipStatus
from applications.models import Application, ApplicationStatus, ApplicationStatusHistory

User = get_user_model()


class ApplicationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='applicant@example.com',
            password='TestPassword123!',
        )
        self.internship = Internship.objects.create(
            title='Data Analyst Intern',
            application_deadline=timezone.now() + timedelta(days=7),
            status=InternshipStatus.ACTIVE,
        )
        self.application = Application.objects.create(
            applicant=self.user,
            internship=self.internship,
            status=ApplicationStatus.SUBMITTED,
        )

    def test_application_creation(self):
        self.assertEqual(self.application.status, ApplicationStatus.SUBMITTED)
        self.assertEqual(self.application.applicant, self.user)

    def test_status_transition_logging(self):
        history = ApplicationStatusHistory.objects.create(
            application=self.application,
            from_status=ApplicationStatus.SUBMITTED,
            to_status=ApplicationStatus.SHORTLISTED,
            changed_by=self.user,
            reason='Passed screening score cutoff',
        )
        self.assertEqual(history.from_status, ApplicationStatus.SUBMITTED)
        self.assertEqual(history.to_status, ApplicationStatus.SHORTLISTED)
