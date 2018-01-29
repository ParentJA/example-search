from django.contrib.postgres.search import SearchVectorField
from django.db import models


class Course(models.Model):
    course_code = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=250)
    description = models.TextField()
    search_vector = SearchVectorField(null=True, blank=True)

    def __str__(self):
        return f'{self.course_code} {self.title}'
