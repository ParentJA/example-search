from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import IntegerField, Q
from django.db.models.expressions import Case, F, Value, When
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .models import Course
from .serializers import CourseSearchSerializer, CourseSerializer


class CourseView(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class CourseSearchView(ListAPIView):
    serializer_class = CourseSearchSerializer

    def get_queryset(self):
        query = self.request.query_params.get('query')
        if query is None:
            return Course.objects.none()
        return Course.objects.annotate(
            exact_rank=Case(
                When(course_code__iexact=query, then=Value(1)),
                When(title__iexact=query, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            ),
            full_text_rank=SearchRank(F('search_vector'), SearchQuery(query)),
            fuzzy_rank=TrigramSimilarity('course_code', query)
        ).filter(
            Q(exact_rank=1) |
            Q(full_text_rank__gte=0.1) |
            Q(fuzzy_rank__gte=0.3)
        ).order_by(
            '-exact_rank',
            '-full_text_rank',
            '-fuzzy_rank',
            'course_code'
        )
