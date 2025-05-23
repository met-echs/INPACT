# urls.py
from django.urls import path
from . import views, api_views

urlpatterns = [
    # ── REST API Endpoints ───────────────────────────────────────────────────
    path('api/analytics/', api_views.DashboardAnalyticsView.as_view(), name='api_analytics'),
    path('api/export-csv/', api_views.ExportApplicationsCSVView.as_view(), name='api_export_csv'),

    # ── Template Views ───────────────────────────────────────────────────────
    path('question/<int:question_id>/', views.question_detail, name='question_detail'),
    path('candidate/<int:candidate_id>/', views.candidate_detail, name='candidate_detail'),
    path('manage-evaluation-criteria/', views.manage_evaluation_criteria, name='manage_evaluation_criteria'),
    path('questions/', views.question_manage_criteria, name='question_manage_criteria'),
    path('high-scores/', views.high_scores, name='high_scores'),
    path('adminlogin/', views.login_page, name='admin_login'),
]

