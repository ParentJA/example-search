from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from example.views import CourseSearchView, CourseView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html')),
    path('api/course/<int:pk>/', CourseView.as_view()),
    path('api/course/search/', CourseSearchView.as_view()),
]
