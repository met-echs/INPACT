"""
accounts/tests.py — Unit tests for Student User & Profile models.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class StudentUserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='student@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe',
        )

    def test_user_creation(self):
        self.assertEqual(self.user.email, 'student@example.com')
        self.assertTrue(self.user.check_password('TestPassword123!'))
        self.assertFalse(self.user.is_email_verified)

    def test_auto_profile_creation(self):
        """Verify StudentProfile is auto-created via signal."""
        self.assertIsNotNone(self.user.profile)
        self.assertEqual(self.user.profile.user, self.user)

    def test_auto_username_generation(self):
        """Verify username is automatically generated from email prefix."""
        self.assertEqual(self.user.username, 'student')
