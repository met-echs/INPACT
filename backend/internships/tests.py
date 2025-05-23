"""
internships/tests.py — Unit tests for Internship model.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from internships.models import Internship, InternshipStatus


class InternshipModelTest(TestCase):
    def setUp(self):
        self.internship = Internship.objects.create(
            title='Backend Engineering Intern',
            company_name='TechCorp',
            location='Remote',
            is_remote=True,
            stipend='₹20,000/month',
            duration_months=6,
            description='Django backend developer role.',
            skills_required='Python, Django, PostgreSQL',
            application_deadline=timezone.now() + timedelta(days=14),
            status=InternshipStatus.ACTIVE,
        )

    def test_internship_creation(self):
        self.assertEqual(self.internship.title, 'Backend Engineering Intern')
        self.assertTrue(self.internship.is_accepting_applications)

    def test_skills_list_parsing(self):
        self.assertEqual(
            self.internship.get_skills_list(),
            ['Python', 'Django', 'PostgreSQL'],
        )
