# quiz/management/commands/import_questions.py
import pandas as pd
from django.core.management.base import BaseCommand
from quiz.models import Quiz, Question, Choice

class Command(BaseCommand):
    help = 'Imports questions from a given Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='The path to the Excel file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        
        try:
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            self.stdout.write(self.style.SUCCESS(f"Đang đọc file: {file_path}"))
            
            for sheet_name in sheet_names:
                self.stdout.write(f"Đang xử lý sheet: '{sheet_name}'...")
                
                quiz, created = Quiz.objects.get_or_create(title=sheet_name)
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Đã tạo đề thi mới: '{sheet_name}'"))
                else:
                    self.stdout.write(self.style.WARNING(f"Đề thi '{sheet_name}' đã tồn tại. Sẽ thêm câu hỏi vào đề này."))
                
                # THAY ĐỔI Ở ĐÂY: Thêm header=None để pandas không đọc dòng đầu tiên làm tiêu đề
                df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                
                question_count = 0
                for index, row in df.iterrows():
                    # THAY ĐỔI Ở ĐÂY: Truy cập dữ liệu bằng chỉ số cột (0, 1, 2...)
                    # Cột B -> chỉ số 1
                    question_text = row.get(1) 
                    if pd.isna(question_text) or not question_text:
                        continue

                    question = Question.objects.create(
                        quiz=quiz,
                        text=str(question_text),
                        # Cột A -> chỉ số 0
                        order=int(row.get(0, index + 1)),
                        explanation=str(row.get(7, '')) 
                    )
                    
                    # Cột C, D, E, F -> chỉ số 2, 3, 4, 5
                    choices_text = [
                        row.get(2), row.get(3),
                        row.get(4), row.get(5)
                    ]
                    
                    # Cột G -> chỉ số 6
                    correct_answer_index = int(row.get(6, 0))

                    for i, choice_text in enumerate(choices_text, 1):
                        if pd.notna(choice_text):
                            Choice.objects.create(
                                question=question,
                                text=str(choice_text),
                                is_correct=(i == correct_answer_index)
                            )
                    question_count += 1
                
                self.stdout.write(self.style.SUCCESS(f"-> Đã nhập thành công {question_count} câu hỏi cho đề thi '{sheet_name}'"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('Lỗi: Không tìm thấy file.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Đã xảy ra lỗi: {e}'))
