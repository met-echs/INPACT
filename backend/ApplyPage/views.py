from django.shortcuts import render
from django.http import JsonResponse
import PyPDF2
from dashboard.models import EvaluationCriteria
from groq import Groq
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
from datetime import datetime
from .models import Candidate
from django.core.mail import send_mail
from django.template.loader import render_to_string

client = Groq(api_key=settings.GROQ_API_KEY)

# Allowed MIME types for resume uploads
ALLOWED_RESUME_CONTENT_TYPES = {'application/pdf'}


def generate_credentials(name: str) -> str:
    """
    Generate a temporary password for a shortlisted candidate.
    Format: FirstName@Year  (e.g. Amil@2026)
    The candidate should be prompted to change this on first login.
    """
    first_name = name.split()[0].capitalize()
    current_year = datetime.now().year
    return f"{first_name}@{current_year}"


def thanku_page(request):
    """Render the post-submission thank-you page."""
    return render(request, "ApplyPage/Thankyou.html")


def upload_resume(request):
    """
    Handle resume upload and AI-based screening.

    POST fields:
        name  — candidate full name
        email — candidate email address
        file  — PDF resume (max 5 MB)

    Flow:
        1. Validate inputs and file (PDF only, max 5 MB).
        2. Save file to media/resumes/.
        3. Extract text via PyPDF2.
        4. Score resume via Groq LLM against EvaluationCriteria.
        5. If score >= 50 → create Candidate, send shortlist email.
        6. If score < 50 or -1 → send rejection/feedback email.
    """
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        file = request.FILES.get('file')

        if not (name and email and file):
            return JsonResponse({"error": "All fields are required."}, status=400)

        # ── File validation ─────────────────────────────────────────────────
        content_type = file.content_type
        if content_type not in ALLOWED_RESUME_CONTENT_TYPES:
            return JsonResponse(
                {"error": "Only PDF files are accepted. Please upload a PDF resume."},
                status=400,
            )

        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 5 * 1024 * 1024)  # 5 MB default
        if file.size > max_size:
            max_mb = max_size // (1024 * 1024)
            return JsonResponse(
                {"error": f"Resume must be smaller than {max_mb} MB."},
                status=400,
            )

        try:
            # ── Save file ────────────────────────────────────────────────────
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'resumes'))
            filename = fs.save(file.name, file)
            file_path = os.path.join('resumes', filename)

            # ── Extract text from PDF ────────────────────────────────────────
            # Reset file pointer after content-type read
            file.seek(0)
            pdf_reader = PyPDF2.PdfReader(file)
            file_content = ""
            for page in pdf_reader.pages:
                file_content += page.extract_text() or ""
            file_content = file_content.strip()

            # ── Fetch evaluation criteria ────────────────────────────────────
            resume_criteria = EvaluationCriteria.objects.first()
            if not resume_criteria:
                return JsonResponse(
                    {"error": "Evaluation criteria not configured. Contact admin."},
                    status=500,
                )

            job_role = resume_criteria.job_role
            min_years_experience = resume_criteria.min_years_experience
            min_projects = resume_criteria.min_projects
            certifications_required = resume_criteria.certifications_required
            w_exp = getattr(resume_criteria, 'weight_experience', 25)
            w_proj = getattr(resume_criteria, 'weight_projects', 25)
            w_cert = getattr(resume_criteria, 'weight_certifications', 25)
            w_ats = getattr(resume_criteria, 'weight_ats', 25)
            cutoff = getattr(resume_criteria, 'shortlist_threshold', 50)

            # ── Build LLM prompt ─────────────────────────────────────────────
            prompt = f"""
You are tasked with evaluating a resume based on the following weighted criteria:

1. **Job Role**: Does the resume clearly specify a relevant job role for: {job_role}?
2. **Work Experience (Weight: {w_exp}%)**: Minimum {min_years_experience} years relevant experience for {job_role}.
3. **Projects (Weight: {w_proj}%)**: Minimum {min_projects} relevant projects.
4. **Certifications (Weight: {w_cert}%)**: Expected certifications: {certifications_required if certifications_required else "None"}.
5. **ATS Friendliness (Weight: {w_ats}%)**: Readable by an Applicant Tracking System.

- Scale each section according to its weight: Experience ({w_exp} pts), Projects ({w_proj} pts), Certifications ({w_cert} pts), ATS ({w_ats} pts).
- If job role is completely irrelevant, cap final score at 40.
- If the resume is **not ATS-friendly**, set the score to **-1**.

Return only the final score as a **number** between -1 and 100, without any explanation.
            """

            # ── Call Groq LLM ────────────────────────────────────────────────
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt + file_content}],
                temperature=0.3,
                max_completion_tokens=2024,
                top_p=1,
                stream=False,
            )
            score = float(completion.choices[0].message.content.strip())
            print(f"[Resume Score] {email}: {score} (Cutoff: {cutoff})")

            from_email = settings.DEFAULT_FROM_EMAIL
            login_url = getattr(settings, 'FRONTEND_URL', 'http://127.0.0.1:8000') + '/interview/login/'

            # ── Shortlisted ──────────────────────────────────────────────────
            if score >= cutoff:
                password = generate_credentials(name)
                subject = "Your Internship Application — Next Steps"
                message = render_to_string('emails/shortlist.html', {
                    'name': name,
                    'email': email,
                    'password': password,
                    'login_url': login_url,
                })
                try:
                    send_mail(subject, '', from_email, [email], html_message=message)
                except Exception as mail_err:
                    print(f"[Email Error] Failed to send shortlist email to {email}: {mail_err}")
                    return JsonResponse({"error": "Resume accepted but failed to send email."}, status=500)

                # ── Persist candidate ────────────────────────────────────────
                try:
                    candidate = Candidate(
                        name=name,
                        email=email,
                        resume_score=int(score),
                        resume_path=file_path,
                    )
                    candidate.set_password(password)  # Hash before saving
                    candidate.save()
                    return JsonResponse({"message": "Resume accepted. Check your email for credentials."}, status=200)
                except Exception as db_err:
                    print(f"[DB Error] Could not save candidate {email}: {db_err}")
                    return JsonResponse(
                        {"error": "Candidate already exists. Please check your email ID."},
                        status=409,
                    )

            # ── Rejected (score < cutoff) ────────────────────────────────────
            elif score >= 0:
                subject = "Application Update: Thank You for Your Submission"
                message = render_to_string('emails/rejection.html', {
                    'name': name,
                })
                try:
                    send_mail(subject, '', from_email, [email], html_message=message)
                    return JsonResponse({"message": "Application reviewed. Check your email for details."}, status=200)
                except Exception as mail_err:
                    print(f"[Email Error] {mail_err}")
                    return JsonResponse({"error": "Failed to send feedback email."}, status=500)

            # ── ATS-unfriendly resume (score == -1) ──────────────────────────
            else:
                subject = "Application Update: Resume Formatting Feedback"
                message = render_to_string('emails/ats_feedback.html', {
                    'name': name,
                })
                try:
                    send_mail(subject, '', from_email, [email], html_message=message)
                    return JsonResponse({"message": "Resume formatting feedback sent to your email."}, status=200)
                except Exception as mail_err:
                    print(f"[Email Error] {mail_err}")
                    return JsonResponse({"error": "Failed to send feedback email."}, status=500)


        except Exception as e:
            print(f"[Resume Upload Error] {e}")
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    # GET → render the upload form
    return render(request, "ApplyPage/Apply.html")
