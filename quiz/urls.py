# quiz/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.exam_list, name='exam_list'),
    path('exam/<int:exam_id>/', views.quiz_list, name='quiz_list'),
    path('quiz/<int:quiz_id>/start/', views.quiz_start, name='quiz_start'),
    path('quiz/<int:quiz_id>/start/all/', views.quiz_start_all, name='quiz_start_all'),
    path('quiz/<int:quiz_id>/question/<int:index>/', views.quiz_question, name='quiz_question'),
    path('quiz/<int:quiz_id>/question/<int:index>/json/', views.quiz_question_json, name='quiz_question_json'),
    path('quiz/check-answer/', views.check_answer, name='check_answer'),
    path('quiz/<int:quiz_id>/review/', views.quiz_review, name='quiz_review'),
    path('quiz/<int:quiz_id>/result/', views.quiz_result, name='quiz_result'),
    path('exam/<int:exam_id>/lookup/', views.question_lookup, name='question_lookup'),
]
