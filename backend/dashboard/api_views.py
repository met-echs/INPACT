"""
dashboard/api_views.py — Recruiter & Admin Analytics API + CSV Data Export.
"""
import csv
from django.http import HttpResponse
from django.db.models import Count, Avg
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.permissions import IsAdminUser

from accounts.models import CustomUser, StudentProfile
from internships.models import Internship
from applications.models import Application, ApplicationStatus


class DashboardAnalyticsView(APIView):
    """
    GET /api/dashboard/analytics/
    Recruiter dashboard analytics & recruitment metric aggregation.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_students = CustomUser.objects.filter(is_staff=False).count()
        total_internships = Internship.objects.count()
        active_internships = Internship.objects.filter(status='active').count()
        total_applications = Application.objects.count()

        # Status breakdown
        status_counts = (
            Application.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        status_dict = {item['status']: item['count'] for item in status_counts}

        # Department breakdown via StudentProfile
        dept_counts = (
            StudentProfile.objects
            .exclude(department='')
            .values('department')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        dept_dict = {item['department']: item['count'] for item in dept_counts}

        # Score averages
        score_stats = Application.objects.aggregate(
            avg_resume=Avg('resume_score'),
            avg_interview=Avg('interview_score'),
            avg_overall=Avg('overall_score'),
        )

        # Top 10 shortlisted/high-scoring applicants
        top_applicants = (
            Application.objects
            .select_related('applicant', 'internship', 'applicant__profile')
            .order_by('-overall_score', '-resume_score')[:10]
        )

        top_list = []
        for app in top_applicants:
            top_list.append({
                'application_id': app.id,
                'student_name': app.applicant.get_full_name() or app.applicant.username,
                'email': app.applicant.email,
                'department': getattr(app.applicant.profile, 'department', ''),
                'internship_title': app.internship.title,
                'status': app.status,
                'resume_score': app.resume_score,
                'interview_score': app.interview_score,
                'overall_score': app.overall_score,
            })

        return Response({
            'overview': {
                'total_students': total_students,
                'total_internships': total_internships,
                'active_internships': active_internships,
                'total_applications': total_applications,
            },
            'applications_by_status': status_dict,
            'applications_by_department': dept_dict,
            'score_statistics': {
                'avg_resume_score': round(score_stats['avg_resume'] or 0, 2),
                'avg_interview_score': round(score_stats['avg_interview'] or 0, 2),
                'avg_overall_score': round(score_stats['avg_overall'] or 0, 2),
            },
            'top_applicants': top_list,
        }, status=status.HTTP_200_OK)


class ExportApplicationsCSVView(APIView):
    """
    GET /api/dashboard/export-csv/
    Generates a CSV export of all candidate applications with scores & profile info.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inpact_applications_report.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Application ID', 'Student Name', 'Email', 'College', 'Department', 'CGPA',
            'Internship Title', 'Company', 'Application Status',
            'Resume Score', 'Interview Score', 'Overall Score', 'Submitted Date',
        ])

        applications = (
            Application.objects
            .select_related('applicant', 'internship', 'applicant__profile')
            .order_by('-submitted_at')
        )

        for app in applications:
            profile = getattr(app.applicant, 'profile', None)
            writer.writerow([
                app.id,
                app.applicant.get_full_name() or app.applicant.username,
                app.applicant.email,
                profile.college if profile else '',
                profile.department if profile else '',
                profile.cgpa if profile else '',
                app.internship.title,
                app.internship.company_name,
                app.get_status_display(),
                app.resume_score or '',
                app.interview_score or '',
                app.overall_score or '',
                app.submitted_at.strftime('%Y-%m-%d %H:%M'),
            ])

        return response
