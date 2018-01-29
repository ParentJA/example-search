from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import migrations


def update_search_vector(apps, schema_editor):
    Course = apps.get_model('example', 'Course')
    Course.objects.all().update(search_vector=(
        SearchVector('course_code', weight='A') +
        SearchVector('title', weight='A') +
        SearchVector('description', weight='C')
    ))


class Migration(migrations.Migration):
    dependencies = [
        ('example', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='search_vector',
            field=SearchVectorField(blank=True, null=True),
        ),
        migrations.RunPython(update_search_vector),
    ]
