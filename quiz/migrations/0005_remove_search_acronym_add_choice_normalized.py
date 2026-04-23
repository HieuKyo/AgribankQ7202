from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0004_question_search_text_normalized'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='question',
            name='search_acronym',
        ),
        migrations.AddField(
            model_name='choice',
            name='search_text_normalized',
            field=models.TextField(blank=True, db_index=True, editable=False),
        ),
    ]
