from django.shortcuts import render, redirect, get_object_or_404
from .models import Quiz, Question # Thêm Question
from datetime import datetime
from django.db.models import Count
from .models import Exam ,Quiz, Question, Choice # Thêm Choice vào
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import random # Thêm import này ở đầu file

def main_home(request):
    # Lấy danh sách các Kỳ thi lớn
    exams = Exam.objects.all()
    context = {
        'exams': exams,
        'now': datetime.now()
    }
    return render(request, 'quiz/main_home.html', context)

def quiz_list(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    # Lấy các chủ đề thuộc về kỳ thi đó
    quizzes = exam.quizzes.all()
    context = {
        'exam': exam,
        'quizzes': quizzes,
        'now': datetime.now()
    }
    return render(request, 'quiz/quiz_list.html', context)

# View mới cho trang làm bài
def quiz_detail(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    
    question_ids = list(quiz.questions.values_list('id', flat=True))
    random.shuffle(question_ids)
    question_ids_to_take = question_ids[:50]
    
    # XÓA SẠCH DỮ LIỆU CŨ VÀ KHỞI TẠO MỚI
    session_prefix = f'quiz_{quiz_id}'
    request.session[f'{session_prefix}_shuffled_ids'] = question_ids_to_take
    request.session[f'{session_prefix}_score'] = 0
    request.session[f'{session_prefix}_total_questions'] = len(question_ids_to_take)
    request.session[f'{session_prefix}_answers'] = {} # Quan trọng: Khởi tạo dictionary rỗng
    request.session['current_quiz_id'] = quiz_id
    
    return redirect('question_view', quiz_id=quiz.id, question_index=0)

# View mới để hiển thị từng câu hỏi
def question_view(request, quiz_id, question_index):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    shuffled_ids = request.session.get(f'quiz_{quiz_id}_shuffled_ids', [])
    
    if not shuffled_ids or question_index >= len(shuffled_ids):
        return redirect('quiz_result', quiz_id=quiz.id)

    question_id = shuffled_ids[question_index]
    question = get_object_or_404(Question, pk=question_id)
    
    next_index = question_index + 1
    is_last_question = next_index >= len(shuffled_ids)

    context = {
        'quiz': quiz,
        'question': question,
        'question_index': question_index,
        'next_index': next_index,
        'is_last_question': is_last_question,
        'now': datetime.now(),
    }
    return render(request, 'quiz/question_view.html', context)

# View mới để kiểm tra câu trả lời qua AJAX
@require_POST
def check_answer(request):
    choice_id = request.POST.get('choice_id')
    choice = get_object_or_404(Choice, pk=choice_id)
    question = choice.question # Lấy câu hỏi từ lựa chọn

    # Tìm đáp án đúng của câu hỏi này
    correct_choice = question.choices.filter(is_correct=True).first()
    if choice.is_correct:
        # Kiểm tra xem đang làm quiz thường hay ngẫu nhiên
        if 'current_quiz_id' in request.session:
            quiz_id = request.session['current_quiz_id']
            session_key = f'quiz_{quiz_id}_score'
            request.session[session_key] = request.session.get(session_key, 0) + 1
        elif 'random_question_ids' in request.session:
            session_key = 'random_quiz_score'
            request.session[session_key] = request.session.get(session_key, 0) + 1
    if 'current_quiz_id' in request.session:
        answers = request.session.get('quiz_answers', {})
        answers[str(question.id)] = choice.id
        request.session['quiz_answers'] = answers
    elif 'random_question_ids' in request.session:
        answers = request.session.get('random_quiz_answers', {})
        answers[str(question.id)] = choice.id
        request.session['random_quiz_answers'] = answers
    # Chuẩn bị dữ liệu để gửi về trình duyệt
    data = {
        'is_correct': choice.is_correct,
        'explanation': question.explanation or "Không có diễn giải cho câu này.",
        # Gửi thêm nội dung của đáp án đúng
        'correct_answer_text': correct_choice.text if correct_choice else "Không tìm thấy đáp án đúng."
    }
    return JsonResponse(data)


def random_quiz(request):
    question_ids = list(
        Question.objects.annotate(num_choices=Count('choices'))
                        .filter(num_choices__gt=0)
                        .order_by('?')
                        .values_list('id', flat=True)[:50]
    )
    
    # XÓA SẠCH DỮ LIỆU CŨ VÀ KHỞI TẠO MỚI
    request.session['random_question_ids'] = question_ids
    request.session['random_quiz_score'] = 0
    request.session['random_quiz_total'] = len(question_ids)
    request.session['random_quiz_answers'] = {} # Quan trọng: Khởi tạo dictionary rỗng
    
    return redirect('random_question_view', question_index=0)


# View mới để xử lý từng câu hỏi ngẫu nhiên
def random_question_view(request, question_index):
    question_ids = request.session.get('random_question_ids', [])
    
    if not question_ids or question_index >= len(question_ids):
        return redirect('random_quiz_result') # Sửa lại để về trang kết quả random

    question_id = question_ids[question_index]
    question = get_object_or_404(Question, pk=question_id)
    
    next_index = question_index + 1
    is_last_question = next_index >= len(question_ids)

    context = {
        'question': question,
        'question_index': question_index,
        'next_index': next_index,
        'is_last_question': is_last_question,
        'quiz_title': "Đề thi Ngẫu nhiên",
        'now': datetime.now(),
    }
    return render(request, 'quiz/random_question_view.html', context)
# View mới để xử lý và chấm điểm
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    
    # Biến để lưu kết quả
    total_questions = quiz.questions.count()
    score = 0
    results = [] # Lưu chi tiết từng câu
    
    if request.method == 'POST':
        for question in quiz.questions.all():
            # Lấy ID của lựa chọn mà người dùng đã chọn cho câu hỏi này
            selected_choice_id = request.POST.get(f'question_{question.id}')
            
            correct_choice = question.choices.filter(is_correct=True).first()
            selected_choice = None
            
            if selected_choice_id:
                selected_choice = Choice.objects.get(pk=selected_choice_id)
                if selected_choice.is_correct:
                    score += 1

            results.append({
                'question': question,
                'correct_choice': correct_choice,
                'selected_choice': selected_choice,
                'is_correct': selected_choice and selected_choice.is_correct,
            })

    context = {
        'quiz': quiz,
        'score': score,
        'total_questions': total_questions,
        'results': results,
        'now': datetime.now(),
    }
    return render(request, 'quiz/quiz_result.html', context)    
def submit_random_quiz(request):
    # Khởi tạo các biến kết quả
    score = 0
    results = []
    
    if request.method == 'POST':
        # Lấy tất cả các câu hỏi đã được trả lời từ form
        question_ids = [key.split('_')[1] for key in request.POST if key.startswith('question_')]
        questions = Question.objects.filter(pk__in=question_ids)
        total_questions = len(questions)

        for question in questions:
            selected_choice_id = request.POST.get(f'question_{question.id}')
            correct_choice = question.choices.filter(is_correct=True).first()
            selected_choice = None
            
            if selected_choice_id:
                selected_choice = Choice.objects.get(pk=selected_choice_id)
                if selected_choice.is_correct:
                    score += 1

            results.append({
                'question': question,
                'correct_choice': correct_choice,
                'selected_choice': selected_choice,
                'is_correct': selected_choice and selected_choice.is_correct,
            })
    
    context = {
        # Dùng một tiêu đề chung thay vì đối tượng quiz
        'quiz_title': "Kết quả Đề thi Ngẫu nhiên",
        'score': score,
        'total_questions': total_questions,
        'results': results,
        'now': datetime.now(),
    }
    # Tái sử dụng template kết quả cũ
    return render(request, 'quiz/quiz_result.html', context)
def quiz_result(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    
    # Lấy điểm, tổng số câu, và chi tiết câu trả lời từ session
    score = request.session.pop(f'quiz_{quiz_id}_score', 0)
    total_questions = request.session.pop(f'quiz_{quiz_id}_total_questions', quiz.questions.count())
    answers = request.session.pop('quiz_answers', {})
    
    # Xóa các session khác để kết thúc bài thi
    request.session.pop('current_quiz_id', None)

    # Lấy ID của các câu hỏi đã được trả lời
    question_ids = answers.keys()
    questions_answered = Question.objects.filter(pk__in=question_ids)
    
    results = []
    for question in questions_answered:
        selected_choice_id = answers.get(str(question.id))
        selected_choice = question.choices.filter(pk=selected_choice_id).first()
        correct_choice = question.choices.filter(is_correct=True).first()
        results.append({
            'question': question,
            'selected_choice': selected_choice,
            'correct_choice': correct_choice,
            'is_correct': selected_choice == correct_choice
        })

    context = {
        'quiz': quiz,
        'score': score,
        'total_questions': total_questions,
        'results': results, # Gửi danh sách kết quả chi tiết tới template
        'now': datetime.now(),
    }
    return render(request, 'quiz/quiz_result.html', context)


def random_quiz_result(request):
    score = request.session.pop('random_quiz_score', 0)
    total_questions = request.session.pop('random_quiz_total', 0)
    answers = request.session.pop('random_quiz_answers', {})
    
    request.session.pop('random_question_ids', None)

    question_ids = answers.keys()
    questions_answered = Question.objects.filter(pk__in=question_ids)
    
    results = []
    for question in questions_answered:
        selected_choice_id = answers.get(str(question.id))
        selected_choice = question.choices.filter(pk=selected_choice_id).first()
        correct_choice = question.choices.filter(is_correct=True).first()
        results.append({
            'question': question,
            'selected_choice': selected_choice,
            'correct_choice': correct_choice,
            'is_correct': selected_choice == correct_choice
        })

    context = {
        'score': score,
        'total_questions': total_questions,
        'quiz_title': "Kết quả Đề thi Ngẫu nhiên",
        'results': results,
        'now': datetime.now(),
    }
    return render(request, 'quiz/random_quiz_result.html', context)