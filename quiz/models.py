# quiz/models.py
from django.db import models
from django.contrib.auth.models import User

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
    order = models.PositiveIntegerField("Thứ tự câu hỏi")
    explanation = models.TextField("Diễn giải / Chú thích", blank=True, null=True)
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Câu {self.order}: {self.text[:50]}..."

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.TextField("Nội dung lựa chọn")
    is_correct = models.BooleanField("Là đáp án đúng", default=False)

    def __str__(self):
        return self.text