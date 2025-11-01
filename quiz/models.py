# quiz/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db import models
from unidecode import unidecode  # <-- 1. THÊM IMPORT NÀY
import re

class Exam(models.Model):
    title = models.CharField("Tên kỳ thi", max_length=255, unique=True)
    description = models.TextField("Mô tả", blank=True)
    
    def __str__(self):
        return self.title

class Quiz(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='quizzes', verbose_name="Kỳ thi")
    
    title = models.CharField("Tên đề thi", max_length=255)
    description = models.TextField("Mô tả", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField("Nội dung câu hỏi")
    order = models.IntegerField("Thứ tự", default=0)
    explanation = models.TextField("Diễn giải", blank=True)

    # 4. THÊM TRƯỜNG MỚI ĐỂ LƯU TỪ VIẾT TẮT
    search_acronym = models.CharField(
        max_length=500, 
        blank=True, 
        editable=False, 
        db_index=True # Đánh index để tìm kiếm nhanh
    )
    # 1. THÊM TRƯỜNG MỚI
    search_text_normalized = models.TextField(
        blank=True, 
        editable=False, 
        db_index=True,
        verbose_name="Nội dung chuẩn hóa"
    )

    def __str__(self):
        return self.text

    # ĐẢM BẢO HÀM SAVE() CỦA BẠN TRÔNG NHƯ THẾ NÀY
    def save(self, *args, **kwargs):
        # Tự động tạo từ viết tắt
        self.search_acronym = _generate_acronym(self.text)
        
        # Tự động tạo nội dung chuẩn hóa (không dấu, chữ thường)
        if self.text:
            self.search_text_normalized = unidecode(self.text.lower())
        else:
            self.search_text_normalized = ""
            
        super().save(*args, **kwargs)

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.TextField("Nội dung lựa chọn")
    is_correct = models.BooleanField("Là đáp án đúng", default=False)

    def __str__(self):
        return self.text

def _generate_acronym(text):
    if not text:
        return ""
    # Chuyển thành chữ thường, không dấu
    text_no_accent = unidecode(text.lower())
    # Lấy tất cả các từ (kể cả số)
    words = re.findall(r'\b\w+\b', text_no_accent)
    # Lấy ký tự đầu tiên của mỗi từ và ghép lại
    acronym = "".join(word[0] for word in words)
    return acronym