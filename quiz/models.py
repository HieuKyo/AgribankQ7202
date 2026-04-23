# quiz/models.py
from django.db import models
from unidecode import unidecode


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
    search_text_normalized = models.TextField(
        blank=True, editable=False, db_index=True, verbose_name="Nội dung chuẩn hóa"
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        self.search_text_normalized = unidecode(self.text.lower()) if self.text else ""
        super().save(*args, **kwargs)


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.TextField("Nội dung lựa chọn")
    is_correct = models.BooleanField("Là đáp án đúng", default=False)
    search_text_normalized = models.TextField(blank=True, editable=False, db_index=True)

    def __str__(self):
        return self.text

    def save(self, *args, **kwargs):
        self.search_text_normalized = unidecode(self.text.lower()) if self.text else ""
        super().save(*args, **kwargs)
