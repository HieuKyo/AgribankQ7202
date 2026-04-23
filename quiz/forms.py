# quiz/forms.py
import os
from django import forms
from .models import Quiz

ALLOWED_EXCEL_EXTENSIONS = {'.xlsx'}
MAX_UPLOAD_SIZE_MB = 5


class ExcelFileField(forms.FileField):
    def validate(self, value):
        super().validate(value)
        if value:
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in ALLOWED_EXCEL_EXTENSIONS:
                raise forms.ValidationError(
                    f"Chỉ chấp nhận file .xlsx. File bạn tải lên có định dạng '{ext}'."
                )
            if value.size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                raise forms.ValidationError(
                    f"File quá lớn. Giới hạn tối đa là {MAX_UPLOAD_SIZE_MB} MB."
                )


class QuestionImportForm(forms.Form):
    quiz = forms.ModelChoiceField(
        queryset=Quiz.objects.all(),
        label="Chọn Đề thi để import câu hỏi vào",
        required=True,
    )
    file = ExcelFileField(label="Chọn file Excel (.xlsx, tối đa 5 MB)")
