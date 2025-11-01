# quiz/management/commands/rebuild_acronyms.py
from django.core.management.base import BaseCommand
from quiz.models import Question

class Command(BaseCommand):
    help = 'Rebuilds the search acronyms for all existing questions'

    def handle(self, *args, **options):
        self.stdout.write('Starting to rebuild acronyms...')
        count = 0
        for question in Question.objects.all():
            question.save() # Gọi save() sẽ tự động kích hoạt logic tạo acronym
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully rebuilt acronyms for {count} questions.'))