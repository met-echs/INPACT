# views.py
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages  # Import the messages module
from .models import EvaluationCriteria
from .forms import EvaluationCriteriaForm
from .models import Question
from .forms import QuestionCriteriaForm
from ApplyPage.models import Candidate
def manage_evaluation_criteria(request):
    criteria_list = EvaluationCriteria.objects.all()
    form = EvaluationCriteriaForm()
    
    if request.method == 'POST':
        # Handle criteria creation
        if 'add_criteria' in request.POST:
            if criteria_list.exists():
                messages.warning(request, "You can only create one set of evaluation criteria.")
                return redirect('manage_evaluation_criteria')
                
            form = EvaluationCriteriaForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Evaluation criteria created successfully!")
                return redirect('manage_evaluation_criteria')
        
        # Handle criteria update
        elif 'update_criteria' in request.POST:
            criteria_id = request.POST.get('criteria_id')
            criteria = get_object_or_404(EvaluationCriteria, id=criteria_id)
            form = EvaluationCriteriaForm(request.POST, instance=criteria)
            if form.is_valid():
                form.save()
                messages.success(request, "Evaluation criteria updated successfully!")
                return redirect('manage_evaluation_criteria')
    
    context = {
        'evaluation_criteria': criteria_list,
        'form': form,
    }
    return render(request, 'dashboard/evaluation_criteria_manage.html', context)


def question_manage_criteria(request):
    if request.method == 'POST':
        if 'add_criteria' in request.POST:
            form = QuestionCriteriaForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'New question criteria added successfully!')
                return redirect('question_manage_criteria')
            else:
                messages.error(request, 'Failed to add question criteria. Please check the form.')
        elif 'delete_criteria' in request.POST:
            criteria_id = request.POST.get('criteria_id')
            criteria = get_object_or_404(Question, id=criteria_id)
            criteria_number = criteria.question_number  # Capture the question number before deleting
            criteria.delete()
            messages.success(request, 'Question criteria deleted successfully!')

            # Find the next question based on the question_number
            next_question = Question.objects.filter(question_number__gt=criteria_number).order_by('question_number').first()
            if next_question:
                return redirect('question_detail', question_id=next_question.id)
            else:
                messages.info(request, 'No next question available.')
                return redirect('question_manage_criteria')
        elif 'delete_all' in request.POST:  
            Question.objects.all().delete()
            messages.success(request, 'All question criteria deleted successfully!')
            return redirect('question_manage_criteria')
    else:
        form = QuestionCriteriaForm()

    # Get all questions ordered by question_number
    criteria_list = Question.objects.all().order_by('question_number')

    return render(request, 'dashboard/question_criteria_manage.html', {
        'form': form,
        'criteria_list': criteria_list
    })

def question_detail(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    return redirect('question_manage_criteria')

def high_scores(request):
    # Get all candidates ordered by resume_score in descending order
    candidates = Candidate.objects.all().order_by('overall_score')

    # Pass the candidate data to the template
    return render(request, 'dashboard/rank.html', {'candidates': candidates})

from .forms import LoginForm
from django.contrib.auth.hashers import check_password as _check_password
from .models import Admin

def login_page(request):
    """
    Admin login view.

    Authenticates against the custom Admin model using Django's password
    hasher (PBKDF2). Credentials are verified via check_password() so
    plaintext is never compared directly against the stored hash.
    """
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                admin = Admin.objects.get(username=username)
                if _check_password(password, admin.password):
                    request.session['admin_logged_in'] = True
                    request.session['admin_username'] = username
                    messages.success(request, "Login successful!")
                    return redirect('high_scores')
                else:
                    messages.error(request, "Invalid username or password.")
            except Admin.DoesNotExist:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid form data.")
        return redirect('admin_login')
    else:
        form = LoginForm()
    return render(request, 'dashboard/Login.html', {'form': form})

from Interview.models import Interview
def candidate_detail(request, candidate_id):
    candidate = get_object_or_404(Candidate, pk=candidate_id)
    interviews = Interview.objects.filter(candidate=candidate)
    question = Question.objects.all()
    return render(request, 'dashboard/candidate_detail.html', {
        'question':question,
        'candidate': candidate,
        'interviews': interviews
    })