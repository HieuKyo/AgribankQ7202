# quiz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URL GỐC (/) sẽ trỏ đến trang chủ mới
    path('', views.main_home, name='main_home'),
    
    # URL DANH SÁCH ĐỀ THI được chuyển đến /quizzes/
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('exam/<int:exam_id>/', views.quiz_list, name='quiz_list'),
    # Các URL khác giữ nguyên
    path('quiz/<int:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<int:quiz_id>/question/<int:question_index>/', views.question_view, name='question_view'),
    path('quiz/<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),
    
    path('quiz/random/', views.random_quiz, name='random_quiz'),
    path('quiz/random/question/<int:question_index>/', views.random_question_view, name='random_question_view'),
    path('quiz/random/result/', views.random_quiz_result, name='random_quiz_result'),
    
    path('quiz/check_answer/', views.check_answer, name='check_answer'),
]