# quiz/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from unidecode import unidecode
import random

from .models import Exam, Quiz, Question, Choice


@login_required
def exam_list(request):
    exams = Exam.objects.annotate(quiz_count=Count('quizzes'))
    return render(request, 'quiz/exam_list.html', {'exams': exams})


@login_required
def quiz_list(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    quizzes = exam.quizzes.annotate(question_count=Count('questions'))
    return render(request, 'quiz/quiz_list.html', {'exam': exam, 'quizzes': quizzes})


@login_required
def quiz_start(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    question_ids = list(quiz.questions.values_list('id', flat=True))
    random.shuffle(question_ids)
    question_ids = question_ids[:50]
    request.session[f'quiz_{quiz_id}_ids'] = question_ids
    request.session[f'quiz_{quiz_id}_answers'] = {}
    return redirect('quiz_question', quiz_id=quiz_id, index=0)


@login_required
def quiz_start_all(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    question_ids = list(quiz.questions.values_list('id', flat=True))
    random.shuffle(question_ids)
    request.session[f'quiz_{quiz_id}_ids'] = question_ids
    request.session[f'quiz_{quiz_id}_answers'] = {}
    return redirect('quiz_question', quiz_id=quiz_id, index=0)


@login_required
def quiz_question(request, quiz_id, index):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    question_ids = request.session.get(f'quiz_{quiz_id}_ids', [])

    if not question_ids or index >= len(question_ids):
        return redirect('quiz_result', quiz_id=quiz_id)

    question = get_object_or_404(Question, pk=question_ids[index])
    answers = request.session.get(f'quiz_{quiz_id}_answers', {})
    selected_choice_id = answers.get(str(question_ids[index]))

    context = {
        'quiz': quiz,
        'question': question,
        'index': index,
        'total': len(question_ids),
        'is_last': index == len(question_ids) - 1,
        'selected_choice_id': int(selected_choice_id) if selected_choice_id else None,
    }
    return render(request, 'quiz/quiz_question.html', context)


@require_POST
def check_answer(request):
    choice_id = request.POST.get('choice_id')
    quiz_id = request.POST.get('quiz_id')

    if not choice_id:
        return JsonResponse({})

    try:
        choice = get_object_or_404(Choice, pk=int(choice_id))
        question = choice.question
        is_correct = choice.is_correct

        if quiz_id:
            session_key = f'quiz_{quiz_id}_answers'
            answers = request.session.get(session_key, {})
            answers[str(question.id)] = choice.id
            request.session[session_key] = answers

        response_data = {
            'is_correct': is_correct,
            'explanation': question.explanation or "Không có diễn giải.",
        }
        if not is_correct:
            correct_choice = question.choices.filter(is_correct=True).first()
            response_data['correct_answer_text'] = correct_choice.text if correct_choice else "Không xác định."

        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def quiz_review(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    question_ids = request.session.get(f'quiz_{quiz_id}_ids', [])
    answers = request.session.get(f'quiz_{quiz_id}_answers', {})

    review_list = [
        {'index': i, 'is_answered': str(q_id) in answers}
        for i, q_id in enumerate(question_ids)
    ]
    return render(request, 'quiz/quiz_review.html', {'quiz': quiz, 'review_list': review_list})


@login_required
def quiz_result(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    question_ids = request.session.get(f'quiz_{quiz_id}_ids', [])
    user_answers = request.session.get(f'quiz_{quiz_id}_answers', {})

    score = 0
    detailed_results = []

    for q_id in question_ids:
        try:
            question = Question.objects.get(pk=q_id)
            correct_choice = question.choices.filter(is_correct=True).first()
            user_choice_id = user_answers.get(str(q_id))
            user_choice = None
            is_correct = False

            if user_choice_id:
                user_choice = Choice.objects.get(pk=int(user_choice_id))
                if user_choice == correct_choice:
                    score += 1
                    is_correct = True

            detailed_results.append({
                'question': question,
                'user_choice': user_choice,
                'correct_choice': correct_choice,
                'is_correct': is_correct,
            })
        except (Question.DoesNotExist, Choice.DoesNotExist):
            continue

    context = {
        'quiz': quiz,
        'score': score,
        'total': len(question_ids),
        'detailed_results': detailed_results,
    }
    return render(request, 'quiz/quiz_result.html', context)


@login_required
def question_lookup(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    questions = []
    query = ""

    if request.method == 'POST':
        query = request.POST.get('query', '')
        if query:
            term = unidecode(query.lower())
            questions = Question.objects.filter(
                quiz__exam_id=exam_id
            ).filter(
                Q(search_text_normalized__icontains=term) |
                Q(choices__search_text_normalized__icontains=term)
            ).prefetch_related('choices').distinct()

    return render(request, 'quiz/question_lookup.html', {
        'exam': exam,
        'questions': questions,
        'query': query,
    })
