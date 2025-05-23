from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from ApplyPage.models import Candidate
from .forms import LoginForm
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import EmailMessage
from groq import Groq
from django.contrib.auth.hashers import check_password as _check_password
import speech_recognition as sr
from dashboard.models import Question, EvaluationCriteria
from .models import Response, Interview
from django.urls import reverse

client = Groq(api_key=settings.GROQ_API_KEY)

# Shared speech recognizer instance (stateless — safe to share)
recognizer = sr.Recognizer()

# Guard microphone initialization — sr.Microphone() fails on headless servers
try:
    microphone = sr.Microphone()
except OSError:
    microphone = None
    import logging
    logging.getLogger(__name__).warning(
        "No audio input device found. Live transcription via server mic is disabled."
    )

# NOTE: The following globals are intentionally kept for backwards compatibility
# with the existing single-user dev setup, but MUST be replaced with session/DB
# storage before deploying to production with concurrent users.
is_transcribing = False
response_text_accumulator = ""

def upload_recording(request):
    print("i am waked")

    if request.method == 'POST' and request.FILES.get('video'):
        print("video is comming")

        try:
            video_file = request.FILES['video']  # Get the uploaded file
            interview_id = request.POST.get('interview_id')  # Get interview_id from request

            if not interview_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Interview ID is required'
                }, status=400)

            # Fetch the existing interview entry
            interview = get_object_or_404(Interview, interview_id=interview_id)

            # Update the video_path field
            interview.video_path = video_file
            interview.save()

            return JsonResponse({
                'status': 'success',
                'path': interview.video_path.url  # Return the URL of the uploaded file
            })

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)  # Return the error message
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method or missing video file'
    }, status=400)

def index(request):
    # Get the interview_id from the GET parameters
    interview_id = request.GET.get("interview_id")
    # You can also validate this if needed.
    return render(request, 'interview/videocall.html', {"interview_id": interview_id})

def endinterview(request):
    user_name = request.session.get('candidate_name', 'Guest') 
    return render(request, 'interview/ExitPage.html', {"name": user_name})


@csrf_exempt
def join_interview(request):
    # Assume the candidate is logged in and candidate_id is stored in the session
    candidate_id = request.session.get('candidate_id')
    if not candidate_id:
        messages.error(request, "You must log in first.")
        return redirect('login')
    
    try:
        candidate = Candidate.objects.get(pk=candidate_id)
    except Candidate.DoesNotExist:
        messages.error(request, "Candidate not found.")
        return redirect('login')
    
    # Retrieve job_role. This may come from a form or be hard-coded.
    # For example, here we hard-code it, but you can get it from request.POST if needed.
    # Retrieve the corresponding EvaluationCriteria instance
    job_role_instance = EvaluationCriteria.objects.first()
    if not job_role_instance:
        print("I AM HERE AT JOIN but it's an error")
        messages.error(request, "Job role not found.")
        return redirect('home')

# Extract the text representation of the job role
    job_role_text = job_role_instance.job_role

# Create an interview instance
    interview = Interview.objects.create(
    candidate=candidate,
    job_role=job_role_text,  # Storing job role as a string
    total_score=0,
    )
    
    # Optionally, store interview_id in session as well (if needed later)
    request.session['interview_id'] = interview.pk
    print('wow i am here')
    # Redirect to the interview page (index view) with the interview_id as a GET parameter
    return redirect(reverse('interview_test') + f'?interview_id={interview.pk}')

def interview_test(request):
    # Get interview_id from the URL query parameters
    interview_id = request.GET.get('interview_id')
    print(f"interview_id:{interview_id}")
    return render(request, 'interview/interview_test.html', {"interview_id": interview_id})
@csrf_exempt
def login_view(request):
    """
    Candidate login view.

    Authenticates using the Candidate model. Passwords are verified via
    check_password() against the stored PBKDF2 hash — plaintext is never
    compared directly.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = Candidate.objects.get(email=username)
                if _check_password(password, user.password):
                    # Store candidate identity in session
                    request.session['candidate_name'] = user.name
                    request.session['candidate_id'] = user.pk
                    return render(request, 'interview/interview_home.html', {'name': user.name})
                else:
                    messages.error(request, "Invalid username or password.")
            except Candidate.DoesNotExist:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid form data.")
        return redirect('login')
    else:
        form = LoginForm()
    return render(request, 'interview/Login.html', {'form': form})

def evaluate_answer(question_text, response_text, specific_area, keywords):
    print("evaluate_answer")
    # print(f"question:{question_text}")
    print(f"response:{response_text}")                                                      
    completion = client.chat.completions.create(
    model="gemma2-9b-it",
    messages=[{
    "role": "system",
    "content": """You are an interviewer tasked with evaluating a candidate's response to a question.
    The response is transcribed from voice and may contain minor inaccuracies. Your task is to assess the answer based on the following:

    *Scoring Rules:*
    1. If the answer is completely empty, irrelevant, or nonsensical, assign a score of 0.
    2. If the answer is mostly incorrect, irrelevant, or poorly structured, assign a score between 1 and 5, with 1 being barely coherent and 5 being partially correct.
    3. If the answer is mostly correct, relevant, and coherent, assign a score between 6 and 10, with 10 being perfectly accurate, logical, and fully addressing the question.

    *Output Rules:*
    - Provide only a numerical score (0-10). 
    - Do not include any text, explanations, or additional comments."""
        }, 
        {
    "role": "user",
    "content": f"""Question: {question_text}
    Specific Area: {specific_area}
    Keywords: {keywords}
    Answer: {response_text}"""
        }],
        temperature=0.7,
        max_tokens=10,
        top_p=1,
        stream=False
    )
    score = completion.choices[0].message.content.strip()

    try:
        score = int(score)
        score = max(0, min(10, score))  # Ensure score is between 0 and 10
    except ValueError:
        score = 0  # Default to 0 if the score is not valid

    print(f"Score: {score}")
    return score



def get_question(request):
    question_number = request.GET.get('question_number')

    if question_number:
        try:
            question_number = int(question_number)
            question = Question.objects.get(question_number=question_number)
        except (Question.DoesNotExist, ValueError):
            print("QUESTION FINSISHED")
            return JsonResponse({
                "error": "Okay, the questions are finished. You can exit the interview.",
                "status": "finished"
            }, status=404)
    else:
        # Fetch the first question based on the smallest question_number
        question = Question.objects.order_by('question_number').first()
        if not question:
            print("QUESTION FINSISHED")
            return JsonResponse({
                "error": "Okay, the questions are finished. You can exit the interview.",
                "status": "finished"
            }, status=404)

    return JsonResponse({
        "question_number": question.question_number,
        "question_text": question.question,
        "status": "ok"
    })


def start_transcription(request):
    global is_transcribing
    global response_text_accumulator
    is_transcribing = True
    response_text_accumulator = ""
    response_data = {"status": "Recording started"}
    print(" I AM STARTING TRANSCRIPTION")
    return JsonResponse(response_data)
import time
@csrf_exempt
def stop_transcription(request):
    """
    This view is called when the candidate stops transcription (either manually via a button or automatically).
    It:
      - Stops the transcription process.
      - Retrieves the current question based on the provided question_number.
      - Retrieves the interview via the 'interview_id' GET parameter (or session as fallback).
      - Evaluates the candidate's response using evaluate_answer.
      - Saves the response (linked to the question and interview).
      - Determines the next question (if any) and returns its data.
    """
    global is_transcribing, response_text_accumulator

    # Stop the transcription process
    is_transcribing = False

    # Get current question number from GET parameters
    current_question_number = request.GET.get('question_number')
    if not current_question_number:
        return JsonResponse({"error": "Question number not provided."}, status=400)

    try:
        current_question_number = int(current_question_number)
        question = Question.objects.get(question_number=current_question_number)
    except (Question.DoesNotExist, ValueError):
        return JsonResponse({"error": "Invalid question number."}, status=404)

    # Retrieve the interview id from GET parameters first, or fallback to session
    interview_id = request.GET.get('interview_id') or request.session.get('interview_id')
    if not interview_id:
        return JsonResponse({"error": "Interview not found."}, status=400)
    try:
        interview = Interview.objects.get(pk=interview_id)
    except Interview.DoesNotExist:
        return JsonResponse({"error": "Interview record not found."}, status=404)

    # Wait a short time to ensure any remaining transcription is processed
    import time
    time.sleep(1)  # Adjust the delay if necessary for synchronization

    # Evaluate the answer using your evaluate_answer function
    score = evaluate_answer(
        question_text=question.question,
        response_text=response_text_accumulator.strip(),
        specific_area=question.specific_area,
        keywords=question.keywords
    )

    # Save the response to the database
    response_obj = Response.objects.create(
        question=question,
        response_text=response_text_accumulator.strip(),
        score=score,
        interview=interview
    )

    # Fetch the next available question based on question_number order
    next_question = Question.objects.filter(question_number__gt=current_question_number).order_by('question_number').first()
    if next_question:
        next_question_number = next_question.question_number
        next_question_text = next_question.question
    else:
        next_question_number = None
        next_question_text = "No more questions."

    # Reset the accumulator for the next question
    response_text_accumulator = ""

    # Return the next question details as JSON
    return JsonResponse({
        "response": response_obj.response_text,
        "score": score,
        "next_question_number": next_question_number,
        "next_question_text": next_question_text
    })




def live_transcribe(request):
    """
    Server-side live transcription endpoint.

    WARNING: This approach uses the server's physical microphone and is only
    functional in a local single-user development setup. In production,
    transcription should be performed client-side (e.g. Web Speech API or
    Deepgram via WebSocket) and the transcribed text POSTed to the server.
    """
    global is_transcribing, response_text_accumulator

    if microphone is None:
        return JsonResponse(
            {"error": "Server-side microphone not available. Use client-side transcription."},
            status=503,
        )

    if is_transcribing:
        try:
            with microphone as source:
                while is_transcribing:
                    try:
                        audio = recognizer.listen(source, timeout=2, phrase_time_limit=5)
                        text = recognizer.recognize_google(audio)
                        response_text_accumulator += " " + text
                    except sr.WaitTimeoutError:
                        pass  # No speech in window — continue listening
                    except sr.UnknownValueError:
                        pass  # Audio unclear — continue listening
                    except sr.RequestError as e:
                        return JsonResponse({"error": f"Speech recognition service error: {e}"})

            return JsonResponse({"transcription": response_text_accumulator})

        except OSError as e:
            return JsonResponse({"error": f"Microphone error: {e}"})
    else:
        return JsonResponse({"error": "Transcription is not active"})



from django.http import JsonResponse
from django.db.models import Sum
from .models import Interview, Response

def no_questions_left(request):
    if request.method == 'POST':
        interview_id = request.session.get('interview_id')
        candidate_id = request.session.get('candidate_id')

        if not interview_id or not candidate_id:
            return JsonResponse({"error": "Interview ID not found in session"}, status=400)

        try:
            # Corrected line: use 'interview_id' instead of 'id'
            interview = Interview.objects.get(interview_id=interview_id)
            candidate = Candidate.objects.get(candidate_id=candidate_id)
            resume_score=candidate.resume_score
            interview_score = Response.objects.filter(interview=interview).aggregate(Sum('score'))['score__sum'] or 0
            interview.total_score = interview_score
            overall_score = resume_score+interview_score
            candidate.overall_score = overall_score
            candidate.save()
            interview.save()

            return JsonResponse({"message": "Total score updated", "total_score": interview_score})

        except Interview.DoesNotExist:
            return JsonResponse({"error": "Interview not found"}, status=404)

    return JsonResponse({"error": "Invalid request"}, status=400)
