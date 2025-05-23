"""
accounts/signals.py — Post-save signals for the accounts app.

Signals auto-create a StudentProfile whenever a new CustomUser is saved,
ensuring every user always has a corresponding profile record.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, StudentProfile


@receiver(post_save, sender=CustomUser)
def create_student_profile(sender, instance: CustomUser, created: bool, **kwargs) -> None:
    """
    Auto-create a StudentProfile for every new CustomUser.

    Triggered after save() completes. `created=True` only on the very first
    save (INSERT), not on subsequent updates (UPDATE).
    """
    if created:
        StudentProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_student_profile(sender, instance: CustomUser, **kwargs) -> None:
    """
    Ensure the related StudentProfile is saved whenever CustomUser is saved.

    Handles the edge case where a profile might exist but not be saved
    (e.g., if a signal was missed during data import).
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
