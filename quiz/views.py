from django.shortcuts import render, redirect, get_object_or_404
from .models import Quiz, Question # Thêm Question
from datetime import datetime
from django.db.models import Count
from .models import Exam ,Quiz, Question, Choice # Thêm Choice vào
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import random # Thêm import này ở đầu file
from unidecode import unidecode
from django.db.models import Q

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
        'previous_index': question_index - 1,
        'next_index': question_index + 1,
        'total_questions': len(shuffled_ids), # THÊM DÒNG NÀY
        'is_last_question': question_index == len(shuffled_ids) - 1,
    }
    return render(request, 'quiz/question_view.html', context)

# View mới để kiểm tra câu trả lời qua AJAX
@require_POST
def check_answer(request):
    choice_id = request.POST.get('choice_id')
    quiz_id = request.POST.get('quiz_id') # Sẽ có nếu là "thi theo chủ đề"
    quiz_mode = request.POST.get('quiz_mode') # Sẽ là 'random' nếu là "thi ngẫu nhiên"

    if not choice_id:
        # Tình huống này xảy ra khi người dùng nhấn "Next" mà không chọn đáp án
        # Chúng ta không cần làm gì cả, chỉ cần trả về một JSON rỗng
        return JsonResponse({})

    try:
        choice = get_object_or_404(Choice, pk=int(choice_id))
        question = choice.question
        is_correct = choice.is_correct
        
        # Xác định đúng session key để lưu đáp án
        if quiz_mode == 'random':
            session_key = 'random_quiz_answers'
        elif quiz_id:
            session_key = f'quiz_{quiz_id}_answers'
        else:
            # Không xác định được ngữ cảnh, không lưu
            return JsonResponse({'error': 'Quiz context not provided'}, status=400)

        # Lấy, cập nhật và lưu lại session
        answers = request.session.get(session_key, {})
        answers[str(question.id)] = choice.id
        request.session[session_key] = answers
        
        # Chuẩn bị dữ liệu trả về cho popup "Kiểm tra Đáp án"
        response_data = {
            'is_correct': is_correct,
            'explanation': question.explanation or "Không có diễn giải."
        }
        
        if not is_correct:
            correct_choice = question.choices.filter(is_correct=True).first()
            response_data['correct_answer_text'] = correct_choice.text if correct_choice else "Không xác định."
            
        return JsonResponse(response_data)

    except Choice.DoesNotExist:
        return JsonResponse({'error': 'Invalid choice'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
    question_ids = request.session.get('random_question_ids', []) # Tên đúng là 'question_ids'

    if not question_ids or question_index >= len(question_ids):
        return redirect('random_quiz_result')

    question_id = question_ids[question_index]
    question = get_object_or_404(Question, pk=question_id)

    # is_last_question và next_index đã bị xóa khỏi đây,
    # chúng sẽ được thêm vào context một cách chính xác

    context = {
        'question': question,
        'question_index': question_index,
        'previous_index': question_index - 1,
        'next_index': question_index + 1,
        'total_questions': len(question_ids), # Sửa lỗi: dùng 'question_ids'
        'is_last_question': question_index == len(question_ids) - 1, # Sửa lỗi: dùng 'question_ids'
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
    
    # Lấy danh sách câu hỏi và đáp án của người dùng từ session
    shuffled_ids = request.session.get(f'quiz_{quiz_id}_shuffled_ids', [])
    user_answers = request.session.get(f'quiz_{quiz_id}_answers', {})
    
    score = 0
    detailed_results = []
    
    for q_id in shuffled_ids:
        try:
            question = Question.objects.get(pk=q_id)
            correct_choice = question.choices.filter(is_correct=True).first()
            
            # Lấy ID đáp án của người dùng (dưới dạng số nguyên)
            user_choice_id_str = user_answers.get(str(q_id))
            user_choice = None
            is_correct = False
            
            if user_choice_id_str:
                user_choice = Choice.objects.get(pk=int(user_choice_id_str))
                if user_choice == correct_choice:
                    score += 1
                    is_correct = True
            
            detailed_results.append({
                'question': question,
                'user_choice': user_choice,
                'correct_choice': correct_choice,
                'is_correct': is_correct,
            })
        except Question.DoesNotExist:
            continue
        except Choice.DoesNotExist:
            continue

    total_questions = len(shuffled_ids)
    
    context = {
        'quiz': quiz,
        'score': score,
        'total_questions': total_questions,
        'detailed_results': detailed_results, # Gửi 'detailed_results'
        'now': datetime.now()
    }
    return render(request, 'quiz/quiz_result.html', context)


def random_quiz_result(request):
    # Lấy danh sách câu hỏi và đáp án của người dùng từ session
    shuffled_ids = request.session.get('random_question_ids', [])
    user_answers = request.session.get('random_quiz_answers', {})
    
    score = 0
    detailed_results = []
    
    for q_id in shuffled_ids:
        try:
            question = Question.objects.get(pk=q_id)
            correct_choice = question.choices.filter(is_correct=True).first()
            
            user_choice_id_str = user_answers.get(str(q_id))
            user_choice = None
            is_correct = False
            
            if user_choice_id_str:
                user_choice = Choice.objects.get(pk=int(user_choice_id_str))
                if user_choice == correct_choice:
                    score += 1
                    is_correct = True
            
            detailed_results.append({
                'question': question,
                'user_choice': user_choice,
                'correct_choice': correct_choice,
                'is_correct': is_correct,
            })
        except Question.DoesNotExist:
            continue
        except Choice.DoesNotExist:
            continue

    total_questions = len(shuffled_ids)
    
    context = {
        'quiz_title': 'Kết quả - Đề thi Ngẫu nhiên', # Gửi 'quiz_title'
        'score': score,
        'total_questions': total_questions,
        'detailed_results': detailed_results, # Gửi 'detailed_results'
        'now': datetime.now()
    }
    return render(request, 'quiz/quiz_result.html', context) # Tái sử dụng template

def review_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, pk=quiz_id)
    shuffled_ids = request.session.get(f'quiz_{quiz_id}_shuffled_ids', [])
    answers = request.session.get(f'quiz_{quiz_id}_answers', {})

    review_list = []
    for index, q_id in enumerate(shuffled_ids):
        review_list.append({
            'index': index,
            'is_answered': str(q_id) in answers
        })

    context = {'quiz': quiz, 'review_list': review_list, 'now': datetime.now()}
    return render(request, 'quiz/review_quiz.html', context)

def review_random_quiz(request):
    shuffled_ids = request.session.get('random_question_ids', [])
    answers = request.session.get('random_quiz_answers', {})

    review_list = []
    for index, q_id in enumerate(shuffled_ids):
        review_list.append({
            'index': index,
            'is_answered': str(q_id) in answers
        })

    context = {'review_list': review_list, 'quiz_title': "Xem lại - Đề thi Ngẫu nhiên", 'now': datetime.now()}
    return render(request, 'quiz/review_quiz.html', context)

def question_lookup(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    questions = []
    query = ""
    
    if request.method == 'POST':
        query = request.POST.get('query', '')
        if query:
            search_term = unidecode(query.lower())
            questions = Question.objects.filter(
                Q(quiz__exam_id=exam_id) & (
                    Q(search_acronym__istartswith=search_term) |
                    Q(search_text_normalized__icontains=search_term) # Đảm bảo bạn đang dùng __icontains
                )
            ).prefetch_related('choices').distinct()

    context = {
        'exam': exam, 
        'questions': questions, 
        'query': query, 
        'now': datetime.now()
    }
    return render(request, 'quiz/question_lookup.html', context)

def about_author(request):
    context = {'now': datetime.now()}
    return render(request, 'quiz/about_author.html', context)