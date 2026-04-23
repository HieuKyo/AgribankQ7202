# quiz/admin.py
import pandas as pd
from unidecode import unidecode
from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Exam, Quiz, Question, Choice
from .forms import QuestionImportForm


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]
    list_display = ('text', 'quiz', 'order')
    list_filter = ('quiz',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_questions_view), name='quiz_question_import'),
        ]
        return custom_urls + urls

    def import_questions_view(self, request):
        if request.method == "POST":
            form = QuestionImportForm(request.POST, request.FILES)
            if form.is_valid():
                quiz = form.cleaned_data['quiz']
                file = request.FILES['file']
                try:
                    df = pd.read_excel(file, header=None)

                    # Lấy tập hợp normalized text đã tồn tại trong toàn bộ kỳ thi
                    exam = quiz.exam
                    existing_normalized = set(
                        Question.objects.filter(quiz__exam=exam)
                        .values_list('search_text_normalized', flat=True)
                    )

                    questions_to_create = []
                    choices_data = []
                    seen_in_file = set()
                    skipped_duplicate = 0

                    for index, row in df.iterrows():
                        question_text = row.get(1)
                        if pd.isna(question_text) or not question_text:
                            continue

                        normalized = unidecode(str(question_text).lower())

                        if normalized in existing_normalized or normalized in seen_in_file:
                            skipped_duplicate += 1
                            continue

                        seen_in_file.add(normalized)

                        explanation = row.get(7, '')
                        if pd.isna(explanation):
                            explanation = ''

                        question = Question(
                            quiz=quiz,
                            text=str(question_text),
                            order=int(row.get(0, index + 1)),
                            explanation=str(explanation),
                            search_text_normalized=normalized,
                        )
                        questions_to_create.append(question)

                        choices_text = [row.get(2), row.get(3), row.get(4), row.get(5)]
                        correct_index = int(row.get(6, 0))
                        choices_data.append((choices_text, correct_index))

                    created_questions = Question.objects.bulk_create(questions_to_create)

                    choices_to_create = []
                    for question, (choices_text, correct_index) in zip(created_questions, choices_data):
                        for i, choice_text in enumerate(choices_text, 1):
                            if pd.notna(choice_text):
                                choices_to_create.append(
                                    Choice(
                                        question=question,
                                        text=str(choice_text),
                                        is_correct=(i == correct_index),
                                        search_text_normalized=unidecode(str(choice_text).lower()),
                                    )
                                )

                    Choice.objects.bulk_create(choices_to_create)

                    count = len(created_questions)
                    self.message_user(
                        request,
                        f"Import thành công {count} câu. Đã bỏ qua {skipped_duplicate} câu trùng.",
                        messages.SUCCESS
                    )
                    return redirect("..")

                except Exception as e:
                    self.message_user(request, f"Đã xảy ra lỗi khi đọc file: {e}", messages.ERROR)
        else:
            form = QuestionImportForm()

        context = self.get_common_context(request)
        context['form'] = form
        context['title'] = "Import Câu hỏi từ Excel"
        return render(request, "admin/quiz/question/import_questions.html", context)

    def get_common_context(self, request):
        return {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
        }


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'exam', 'created_at')
    list_filter = ('exam',)
