from django.contrib import admin
from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    fields = ('id', 'course_code', 'title', 'description', 'search_vector',)
    list_display = ('id', 'course_code', 'title',)
    readonly_fields = ('id', 'search_vector',)
