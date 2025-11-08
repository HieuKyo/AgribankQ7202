# quiz/admin.py
import pandas as pd
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
                    
                    questions_to_create = []
                    choices_to_create = []
                    
                    # Dùng một danh sách (list) để lưu trữ tạm
                    # dữ liệu lựa chọn theo đúng thứ tự
                    temp_choice_data = [] 

                    for index, row in df.iterrows():
                        question_text = row.get(1)
                        if pd.isna(question_text) or not question_text:
                            continue

                        # 1. Chuẩn bị Question object trong bộ nhớ (chưa lưu)
                        question = Question(
                            quiz=quiz,
                            text=str(question_text),
                            order=int(row.get(0, index + 1)),
                            explanation=str(row.get(7, ''))
                        )
                        questions_to_create.append(question)
                        
                        # 2. Lưu tạm dữ liệu choice vào danh sách
                        choices_text = [row.get(2), row.get(3), row.get(4), row.get(5)]
                        correct_answer_index = int(row.get(6, 0))
                        
                        temp_choice_data.append((choices_text, correct_answer_index))

                    # 3. Gửi 1 lệnh duy nhất để tạo TẤT CẢ câu hỏi
                    # (Hàm save() tùy chỉnh sẽ được gọi cho từng cái)
                    created_questions = Question.objects.bulk_create(questions_to_create)
                    
                    # 4. Lặp lại các câu hỏi đã tạo (giờ đã có ID)
                    # created_questions và temp_choice_data là 2 danh sách song song
                    # có cùng thứ tự và cùng số lượng
                    
                    if len(created_questions) != len(temp_choice_data):
                        # Lỗi logic nếu 2 danh sách không bằng nhau
                        raise Exception("Lỗi đồng bộ: Số lượng câu hỏi tạo ra không khớp với dữ liệu lựa chọn.")

                    for question, choice_data in zip(created_questions, temp_choice_data):
                        # Lấy lại dữ liệu choice đã lưu tạm
                        choices_text, correct_index = choice_data
                        
                        for i, choice_text in enumerate(choices_text, 1):
                            if pd.notna(choice_text):
                                # 5. Chuẩn bị Choice object trong bộ nhớ
                                choices_to_create.append(
                                    Choice(
                                        question=question,
                                        text=str(choice_text),
                                        is_correct=(i == correct_index)
                                    )
                                )

                    # 6. Gửi 1 lệnh duy nhất để tạo TẤT CẢ lựa chọn
                    Choice.objects.bulk_create(choices_to_create)
                    
                    question_count = len(created_questions)
                    self.message_user(request, f"Đã import TỐC ĐỘ CAO thành công {question_count} câu hỏi vào đề thi '{quiz.title}'.", messages.SUCCESS)
                    return redirect("..")
                
                except Exception as e:
                    self.message_user(request, f"Đã xảy ra lỗi khi đọc file (lỗi tối ưu): {e}", messages.ERROR)
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
# admin.site.register(Question, QuestionAdmin) # Dòng này không cần nữa vì đã có @admin.register(Question)