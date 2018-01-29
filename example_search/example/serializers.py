from rest_framework import serializers
from .models import Course


class CourseSearchSerializer(serializers.ModelSerializer):
    exact_rank = serializers.IntegerField()
    full_text_rank = serializers.FloatField()
    fuzzy_rank = serializers.FloatField()

    class Meta:
        model = Course
        fields = ('id', 'course_code', 'title', 'exact_rank', 'full_text_rank', 'fuzzy_rank',)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'course_code', 'title', 'description',)
