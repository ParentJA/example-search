from django.contrib.postgres.search import SearchVector
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Course


@receiver(post_save, sender=Course)
def update_search_vector(sender, instance, *args, **kwargs):
    sender.objects.filter(pk=instance.id).update(search_vector=(
        SearchVector('course_code', weight='A') +
        SearchVector('title', weight='A') +
        SearchVector('description', weight='C')
    ))
