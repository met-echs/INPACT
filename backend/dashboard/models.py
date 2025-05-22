# models.py
from django.db import models

class EvaluationCriteria(models.Model):
    job_role = models.CharField(max_length=255)
    min_years_experience = models.IntegerField(default=0)
    min_projects = models.IntegerField(default=0)
    certifications_required = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.job_role

class Question(models.Model):
    question_number = models.IntegerField(unique=True)
    question = models.TextField()
    specific_area = models.CharField(max_length=255)
    keywords = models.TextField(help_text="Comma-separated keywords")
    
    def __str__(self):
        return self.question_text
from django.contrib.auth.hashers import make_password

class Admin(models.Model):
    username = models.EmailField(unique=True, verbose_name="Email Address")
    password = models.CharField(max_length=255, verbose_name="Password")

    def save(self, *args, **kwargs):
        if not self.pk or Admin.objects.get(pk=self.pk).password != self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
