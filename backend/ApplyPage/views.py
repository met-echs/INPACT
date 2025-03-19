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
from backend.settings import GROQ_API_KEY
client = Groq(api_key=GROQ_API_KEY)

def generate_credentials(name):
    """Generate a random username and password."""
    first_name = name.split()[0].capitalize()
    current_year = datetime.now().year  # Get the current year
    password = f"{first_name}@{current_year}"
    return password

def thanku_page(request):
    return render(request,"ApplyPage/Thankyou.html")

def upload_resume(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        file = request.FILES.get('file')
        
        if name and email and file:
            try:
                fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'resumes'))
                filename = fs.save(file.name, file)
                file_path = os.path.join('resumes', filename)
                
                # Read the content of the uploaded PDF file
                pdf_reader = PyPDF2.PdfReader(file)
                file_content = ""
                
                # Extract text from each page of the PDF
                for page in pdf_reader.pages:
                    file_content += page.extract_text()
                
                # Clean up the extracted text (optional)
                file_content = file_content.strip()
                
                # Fetch the first evaluation criteria
                resume_criteria = EvaluationCriteria.objects.first()

                # Extract relevant fields from the evaluation criteria
                job_role = resume_criteria.job_role
                min_years_experience = resume_criteria.min_years_experience
                min_projects = resume_criteria.min_projects
                certifications_required = resume_criteria.certifications_required

                resume_text = file_content

                # Define the evaluation prompt
                prompt = f"""
                You are tasked with evaluating a resume based on the following criteria:

1. **Job Role**: Does the resume clearly specify a relevant job role for the position? The expected job role is: {job_role}.
2. **Work Experience**: Does the resume list at least {min_years_experience} years of relevant work experience related to the job role: {job_role}? Give extra 5 points if the experience is highly relevant.
3. **Number of Projects**: Does the resume list at least {min_projects} relevant projects related to the job role: {job_role}?
4. **Certifications**: Does the resume include relevant certifications? The expected certifications are: {certifications_required if certifications_required else "None"}.
5. **ATS Friendliness**: Is the resume formatted in a way that would be readable by an Applicant Tracking System (ATS)?

- Each of the four criteria (job role, work experience, number of projects, and certifications) will be rated from 0 to 25, and their total score will contribute to a final score out of 100.
- If any of the criteria are missing or poorly satisfied, reduce the score accordingly.
- If the job role criteria is not satisfied, set the overall score to 40.
- If the resume is **not ATS-friendly**, set the score to **-1**.

Return only the final score as a **number** between -1 and 100, without any explanation or breakdown.
                """

                # Request completion from the model
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",  # Use the best model for this task
                    messages=[{"role": "user", "content": prompt + resume_text}],
                    temperature=0.3,  # Use a lower temperature for consistent evaluation
                    max_completion_tokens=2024,
                    top_p=1,
                    stream=False,  # Set to False since we only need the final score
                )
                score = float(completion.choices[0].message.content.strip())
                print(f"Score: {score}")

                if score >= 50:
                    # Generate a random username and password
                    password = generate_credentials(name)
                    print(password)
                    subject = "Your Account Details"
                    img_src = "https://img.freepik.com/free-vector/job-interview-conversation_74855-7566.jpg"
                    message = f"""
                        <html>
                        <head>
                            <title>Welcome Email</title>
                        </head>
                        <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                            <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.2); text-align: center;">
                                <img src="{img_src}" alt="Your Logo" style="max-width: 100%; height: auto; display: block; margin: 0 auto 20px auto; border-radius: 10px;">
                                <h2 style="color: #333;">Hello {name},</h2>
                                <p style="color: #777;">Thank you for uploading your resume.</p>
                                <p style="color: #777;">Here are your account details:</p>
                                <p style="color: #777;"><strong>Username:</strong> {email}</p>
                                <p style="color: #777;"><strong>Password:</strong> {password}</p>
                                <a href="http://127.0.0.1:8000/interview/login/?username={email}&password={password}" 
                                style="background-color: #4CAF50; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px;">
                                Login Now to attend the interview
                                </a>
                                <p style="color: #777;">Best regards,<br>Your Team</p>
                            </div>
                        </body>
                        </html>
                        """
                    from_email = 'your_email@gmail.com'
                    recipient_list = [email]

                    try:
                        send_mail(subject, '', from_email, recipient_list, html_message=message)
                        try:
                            Candidate.objects.create(
                            name=name,
                            email=email,
                            password=password,
                            resume_score=score,
                            resume_path=file_path,
                            created_at=datetime.now()
                            )
                            return JsonResponse({"error": "Candidate already exists. Please check your email ID and try again."}, status=500)
                        except Exception as e:
                            return JsonResponse({"error": "Resume uploaded and email sent successfully"}, status=500)
                    except Exception as e:
                        print(f"Error sending email: {e}")
                        return JsonResponse({"error": "Failed to send Email."}, status=500)

                    
                    # eturn JsonResponse({"error": "Candidate already exists. Please check your email ID and try again."}, status=500)

                elif score < 50:
                    subject = "Application Update: Thank You for Your Submission"
                    img_src = "https://img.freepik.com/free-vector/rejection-concept-illustration_114360-4667.jpg"
                    message = f"""
    <html>
    <head>
        <title>Application Rejection Email</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.2); text-align: center;">
            <img src="{img_src}" alt="Rejection Illustration" style="max-width: 100%; height: auto; display: block; margin: 0 auto 20px auto; border-radius: 10px;">
            <h2 style="color: #333;">Hello {name},</h2>
            <p style="color: #777;">Thank you for taking the time to submit your resume for evaluation. We appreciate the effort you have put into your application.</p>
            <p style="color: #777;">Unfortunately, after careful review, we regret to inform you that your resume did not meet the minimum criteria for the position.</p>
            <p style="color: #777;">Please do not be discouraged. We encourage you to continue building your skills and experience and to apply again in the future. We wish you all the best in your career endeavors.</p>
            <p style="color: #777;">Best regards,<br>Your Team</p>
        </div>
    </body>
    </html>
    """
                    from_email = 'your_email@gmail.com'
                    recipient_list = [email]
                    try:
                        send_mail(subject, '', from_email, recipient_list, html_message=message)
                        return JsonResponse({"error": "Email sent successfully"}, status=500)
                    except Exception as e:
                        print(f"Error sending email: {e}")
                        return JsonResponse({"error": "Failed to send Email."}, status=500)

                elif score == -1:
                    subject = "Application Update: Resume Submission"
                    img_src = "https://img.freepik.com/free-vector/application-concept-illustration_114360-747.jpg"
                    message = f"""
    <html>
    <head>
        <title>Application Feedback</title>
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0 0 15px rgba(0, 0, 0, 0.2); text-align: center;">
            <img src="{img_src}" alt="Application Feedback Illustration" style="max-width: 100%; height: auto; display: block; margin: 0 auto 20px auto; border-radius: 10px;">
            <h2 style="color: #333;">Hello {name},</h2>
            <p style="color: #777;">Thank you for submitting your resume for our evaluation. We truly appreciate the time and effort you invested in the process.</p>
            <p style="color: #777;">Upon review, we noticed that your resume is not optimized for Applicant Tracking Systems (ATS). This may have impacted its readability during the evaluation process.</p>
            <p style="color: #777;">We recommend reformatting your resume to ensure it meets ATS-friendly standards. This typically involves using simple layouts, clear headings, and avoiding complex formatting or graphics.</p>
            <p style="color: #777;">We encourage you to resubmit your resume after making these changes. Please feel free to reach out if you need further guidance or support.</p>
            <p style="color: #777;">Best regards,<br>Your Team</p>
        </div>
    </body>
    </html>
    """
                    from_email = 'your_email@gmail.com'
                    recipient_list = [email]

                    try:
                        send_mail(subject, '', from_email, recipient_list, html_message=message)
                        return JsonResponse({"error": "Email sent successfully"}, status=500)
                    except Exception as e:
                        print(f"Error sending email: {e}")
                        return JsonResponse({"error": "Failed to send Email."}, status=500)

            except Exception as e:
                return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)
        else:
            return JsonResponse({"error": "All fields are required."}, status=400)

    # For GET request, render the form
    return render(request, "ApplyPage/Apply.html")
