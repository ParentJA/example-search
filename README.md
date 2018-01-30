# Full Text Search with Django, PostgreSQL, and Angular (Part I)

(Intro here.)

## Objectives

(Objectives here.)

## Project Setup

(Project setup here.)

```
computer$ mkvirtualenv example-search
(example-search) computer$ pip install django djangorestframework psycopg2
(example-search) computer$ django-admin startproject example_search
(example-search) computer$ cd example_search
(example-search) computer$ python manage.py startapp example
(example-search) computer$ createuser -d -e -W example_search
Password: password
CREATE ROLE example_search NOSUPERUSER CREATEDB NOCREATEROLE INHERIT LOGIN;
(example-search) computer$ createdb -e -O "example_search" example_search
CREATE DATABASE example_search OWNER example_search;
(example-search) computer$ export DB_NAME=example_search
(example-search) computer$ export DB_USER=example_search
(example-search) computer$ export DB_PASS=password
```

**example_search/settings.py**

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASS'),
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

Add `rest_framework` and `example` to `INSTALLED_APPS`.

**example/models.py**

```python
from django.db import models


class Course(models.Model):
    course_code = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=250)
    description = models.TextField()

    def __str__(self):
        return f'{self.course_code} {self.title}'
```

```
(example-search) computer$ python manage.py makemigrations
Migrations for 'example':
  example/migrations/0001_initial.py
    - Create model Course
(example-search) computer$ python manage.py migrate
(example-search) computer$ python loaddata ./example/fixtures/courses.json
(example-search) computer$ psql -U example_search
example_search=# SELECT count(*)
example_search-#   FROM example_course;
 count 
-------
   522
(1 row)

example_search=# CREATE EXTENSION pg_trgm;
example_search=# SELECT show_trgm('hello');
            show_trgm            
---------------------------------
 {"  h"," he",ell,hel,llo,"lo "}
(1 row)

example_search=# \q
(example-search) computer$ python manage.py createsuperuser
```

**example/admin.py**

```python
from django.contrib import admin
from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    fields = ('id', 'course_code', 'title', 'description',)
    list_display = ('id', 'course_code', 'title',)
    readonly_fields = ('id',)
```

**example/serializers.py**

```python
from rest_framework import serializers
from .models import Course


class CourseSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'course_code', 'title',)
```

**example/views.py**

```python
from rest_framework.generics import ListAPIView
from .models import Course
from .serializers import CourseSearchSerializer


class CourseSearchView(ListAPIView):
    serializer_class = CourseSearchSerializer

    def get_queryset(self):
        query = self.request.query_params.get('query')
        if query is None:
            return Course.objects.none()
        return Course.objects.all()
```

**example_search/urls.py**

```python
from django.contrib import admin
from django.urls import path
from example.views import CourseSearchView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/course/search/', CourseSearchView.as_view()),
]

```

## Basic Search

(Basic search here.)

**example/views.py**

```python
from rest_framework.generics import ListAPIView
from django.db.models import Q
from .models import Course
from .serializers import CourseSearchSerializer


class CourseSearchView(ListAPIView):
    serializer_class = CourseSearchSerializer

    def get_queryset(self):
        query = self.request.query_params.get('query')
        if query is None:
            return Course.objects.none()
        return Course.objects.filter(
            Q(course_code=query) | 
            Q(title=query) | 
            Q(description=query)
        )
```

```sql
SELECT id, course_code, title
  FROM example_course
 WHERE course_code = 'Animal Biology' 
    OR title = 'Animal Biology' 
    OR description = 'Animal Biology';
```

```
example_search=# SELECT id, course_code, title
example_search-#   FROM example_course
example_search-#  WHERE course_code = 'Animal Biology' 
example_search-#     OR title = 'Animal Biology' 
example_search-#     OR description = 'Animal Biology';
 id  | course_code |     title      
-----+-------------+----------------
 459 | BIOL221     | Animal Biology
(1 row)
```

## Full Text Search

(Full text search here.)

A basic search works fine when your query matches a field's value exactly, but what about when your query matches part of the value? You might point to the `contains` lookup expression. But wouldn't it be nice if when you searched for "biology", your query matched "biological" too?

**example/views.py**

```python
from rest_framework.generics import ListAPIView
from django.contrib.postgres.search import SearchQuery, SearchVector
from .models import Course
from .serializers import CourseSearchSerializer


class CourseSearchView(ListAPIView):
    serializer_class = CourseSearchSerializer

    def get_queryset(self):
        query = self.request.query_params.get('query')
        if query is None:
            return Course.objects.none()
        search_vector = (
            SearchVector('course_code') + 
            SearchVector('title') + 
            SearchVector('description')
        )
        return Course.objects.annotate(
            search_vector=search_vector
        ).filter(search_vector=SearchQuery(query))
```

```sql
WITH courses AS (
  SELECT id, course_code, title, description, 
         (
           to_tsvector(course_code) || 
           to_tsvector(title) || 
           to_tsvector(description)
         ) AS search_vector
    FROM example_course
)
SELECT id, course_code, title
  FROM courses
 WHERE search_vector @@ plainto_tsquery('biology');
```

```
example_search=# WITH courses AS (
example_search(#   SELECT id, course_code, title, description, 
example_search(#          (
example_search(#            to_tsvector(course_code) || 
example_search(#            to_tsvector(title) || 
example_search(#            to_tsvector(description)
example_search(#          ) AS search_vector
example_search(#     FROM example_course
example_search(# )
example_search-# SELECT id, course_code, title
example_search-#   FROM courses
example_search-#  WHERE search_vector @@ plainto_tsquery('biology');
 id  | course_code |             title             
-----+-------------+-------------------------------
   1 | BIOL112     | General Biology I
   2 | BIOL113     | General Biology II
  61 | PSYC646     | Lifespan Development
  77 | PSYC232     | Developmental Psychology
 323 | ENVR233     | Soil Science
 448 | BIOL498     | Cancer Biology
 453 | BIOL312     | Cell Biology
 454 | BIOL294     | Anatomy and Physiology II Lab
 455 | BIOL293     | Anatomy and Physiology I Lab
 456 | BIOL224     | Plant Biology Lab
 457 | BIOL223     | Animal Biology Lab
 458 | BIOL222     | Plant Biology
 459 | BIOL221     | Animal Biology
(13 rows)
```

## Ranking

(Ranking here.)

**example/views.py**

```python
from rest_framework.generics import ListAPIView
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from .models import Course
from .serializers import CourseSearchSerializer


class CourseSearchView(ListAPIView):
    serializer_class = CourseSearchSerializer

    def get_queryset(self):
        query = self.request.query_params.get('query')
        if query is None:
            return Course.objects.none()
        search_vector = (
            SearchVector('course_code', weight='B') + 
            SearchVector('title', weight='A') + 
            SearchVector('description', weight='C')
        )
        search_query = SearchQuery(query)
        return Course.objects.annotate(
            rank=SearchRank(search_vector, search_query)
        ).filter(rank__gte=0.1).order_by('-rank', 'course_code')
```

```sql
WITH courses AS (
  SELECT id, course_code, title, description, ts_rank(
         (
           setweight(to_tsvector(course_code), 'B') || 
           setweight(to_tsvector(title), 'A') || 
           setweight(to_tsvector(description), 'C')
         ),
         plainto_tsquery('biology')) AS rank
    FROM example_course
)
SELECT id, course_code, title, rank
  FROM courses
 WHERE rank >= 0.1
 ORDER BY rank DESC, course_code ASC;
```

```
example_search=# WITH courses AS (
example_search(#   SELECT id, course_code, title, description, ts_rank(
example_search(#          (
example_search(#            setweight(to_tsvector(course_code), 'B') || 
example_search(#            setweight(to_tsvector(title), 'A') || 
example_search(#            setweight(to_tsvector(description), 'C')
example_search(#          ),
example_search(#          plainto_tsquery('biology')) AS rank
example_search(#     FROM example_course
example_search(# )
example_search-# SELECT id, course_code, title, rank
example_search-#   FROM courses
example_search-#  WHERE rank >= 0.1
example_search-#  ORDER BY rank DESC, course_code ASC;
 id  | course_code |             title             |   rank   
-----+-------------+-------------------------------+----------
   1 | BIOL112     | General Biology I             | 0.638323
 448 | BIOL498     | Cancer Biology                | 0.638323
   2 | BIOL113     | General Biology II            | 0.607927
 459 | BIOL221     | Animal Biology                | 0.607927
 458 | BIOL222     | Plant Biology                 | 0.607927
 457 | BIOL223     | Animal Biology Lab            | 0.607927
 456 | BIOL224     | Plant Biology Lab             | 0.607927
 453 | BIOL312     | Cell Biology                  | 0.607927
 455 | BIOL293     | Anatomy and Physiology I Lab  | 0.121585
 454 | BIOL294     | Anatomy and Physiology II Lab | 0.121585
 323 | ENVR233     | Soil Science                  | 0.121585
  77 | PSYC232     | Developmental Psychology      | 0.121585
  61 | PSYC646     | Lifespan Development          | 0.121585
(13 rows)
```

## Optimization

(Optimization here.)

**example/models.py**

```python
from django.contrib.postgres.search import SearchVectorField
from django.db import models


class Course(models.Model):
    course_code = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=250)
    description = models.TextField()
    search_vector = SearchVectorField(null=True, blank=True)

    def __str__(self):
        return f'{self.course_code} {self.title}'
```

```
python manage.py makemigrations
```

**example/migrations/0002_course_search_vector.py**

```python
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
```

```
python manage.py migrate
```

**example/signals.py**

```python
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
```

**example/__init__.py**

```python
default_app_config = 'example.apps.ExampleConfig'
```

**example/apps.py**

```python
from django.apps import AppConfig


class ExampleConfig(AppConfig):
    name = 'example'

    def ready(self):
        import example.signals
```

## Fuzzy Search

(Fuzzy search here.)

**example/views.py**

```python
from rest_framework.generics import ListAPIView
from django.contrib.postgres.search import TrigramSimilarity
from .models import Course
from .serializers import CourseSearchSerializer


class CourseSearchView(ListAPIView):
    serializer_class = CourseSearchSerializer

    def get_queryset(self):
        query = self.request.query_params.get('query')
        if query is None:
            return Course.objects.none()
        return Course.objects.annotate(
            similarity=TrigramSimilarity('title', query)
        ).filter(rank__gte=0.3).order_by('-similarity')
```

```sql
SELECT id, course_code, title, similarity(title, 'bilogy') AS similarity
  FROM example_course
 WHERE similarity(title, 'bilogy') >= 0.3
 ORDER BY similarity DESC;
```

```
example_search=# SELECT id, course_code, title, similarity(title, 'bilogy') AS similarity
example_search-#   FROM example_course
example_search-#  WHERE similarity(title, 'bilogy') >= 0.3
example_search-#  ORDER BY similarity DESC;
 id  | course_code |     title     | similarity 
-----+-------------+---------------+------------
 453 | BIOL312     | Cell Biology  |   0.333333
 458 | BIOL222     | Plant Biology |     0.3125
(2 rows)
```

## Putting It All Together

(Putting it all together here.)

**example/views.py**

```python
from rest_framework.generics import ListAPIView
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import IntegerField, Q
from django.db.models.expressions import Case, F, Value, When
from .models import Course
from .serializers import CourseSearchSerializer


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
```

```sql
WITH courses AS (
  SELECT id, course_code, title, description, search_vector, 
         CASE  
           WHEN UPPER(course_code) = UPPER('biology') THEN 1 
           WHEN UPPER(title) = UPPER('biology') THEN 1 
           ELSE 0 
         END AS exact_rank, 
         ts_rank(search_vector, plainto_tsquery('biology')) AS full_text_rank, 
         similarity(course_code, 'biology') AS fuzzy_rank
    FROM example_course
)
SELECT id, course_code, title, exact_rank, full_text_rank, fuzzy_rank
  FROM courses
 WHERE exact_rank = 1
    OR full_text_rank >= 0.1
    OR fuzzy_rank >= 0.3
 ORDER BY exact_rank DESC, full_text_rank DESC, fuzzy_rank DESC, course_code ASC;
```

```
example_search=# WITH courses AS (
example_search(#   SELECT id, course_code, title, description, search_vector, 
example_search(#          CASE  
example_search(#            WHEN UPPER(course_code) = UPPER('biology') THEN 1 
example_search(#            WHEN UPPER(title) = UPPER('biology') THEN 1 
example_search(#            ELSE 0 
example_search(#          END AS exact_rank, 
example_search(#          ts_rank(search_vector, plainto_tsquery('biology')) AS full_text_rank, 
example_search(#          similarity(course_code, 'biology') AS fuzzy_rank
example_search(#     FROM example_course
example_search(# )
example_search-# SELECT id, course_code, title, exact_rank, full_text_rank, fuzzy_rank
example_search-#   FROM courses
example_search-#  WHERE exact_rank = 1
example_search-#     OR full_text_rank >= 0.1
example_search-#     OR fuzzy_rank >= 0.3
example_search-#  ORDER BY exact_rank DESC, full_text_rank DESC, fuzzy_rank DESC, course_code ASC;
 id  | course_code |             title             | exact_rank | full_text_rank | fuzzy_rank 
-----+-------------+-------------------------------+------------+----------------+------------
   1 | BIOL112     | General Biology I             |          0 |       0.638323 |   0.333333
 448 | BIOL498     | Cancer Biology                |          0 |       0.638323 |   0.333333
   2 | BIOL113     | General Biology II            |          0 |       0.607927 |   0.333333
 459 | BIOL221     | Animal Biology                |          0 |       0.607927 |   0.333333
 458 | BIOL222     | Plant Biology                 |          0 |       0.607927 |   0.333333
 457 | BIOL223     | Animal Biology Lab            |          0 |       0.607927 |   0.333333
 456 | BIOL224     | Plant Biology Lab             |          0 |       0.607927 |   0.333333
 453 | BIOL312     | Cell Biology                  |          0 |       0.607927 |   0.333333
 455 | BIOL293     | Anatomy and Physiology I Lab  |          0 |       0.121585 |   0.333333
 454 | BIOL294     | Anatomy and Physiology II Lab |          0 |       0.121585 |   0.333333
 323 | ENVR233     | Soil Science                  |          0 |       0.121585 |          0
  77 | PSYC232     | Developmental Psychology      |          0 |       0.121585 |          0
  61 | PSYC646     | Lifespan Development          |          0 |       0.121585 |          0
 452 | BIOL345     | Range and Wildland Plants     |          0 |              0 |   0.333333
 451 | BIOL472     | Biochemistry I: Foundations   |          0 |              0 |   0.333333
 450 | BIOL492     | Physiology                    |          0 |              0 |   0.333333
 449 | BIOL493     | Human Anatomy Laboratory      |          0 |              0 |   0.333333
(17 rows)

```

# Full Text Search with Django, PostgreSQL, and Angular (Part II)

(Intro here.)

## Objectives

(Objectives here.)

## Project Setup

(Project setup here.)

```
ng new example-search
npm install bootstrap bootswatch jquery popper.js
```

**.angular-cli.json**

```json
"styles": [
  "../node_modules/bootswatch/dist/lumen/bootstrap.min.css",
  "styles.css"
],
"scripts": [
  "../node_modules/jquery/dist/jquery.min.js",
  "../node_modules/popper.js/dist/umd/popper.min.js",
  "../node_modules/bootstrap/dist/js/bootstrap.min.js"
]
```

**src/app/app.component.ts**

```javascript
import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html'
})
export class AppComponent {
  title = 'app';
}
```

**src/app/app.component.htmlts**

```html
<router-outlet></router-outlet>
```

## Course Search

(Course search here.)

**example/serializers.py**

```python
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'course_code', 'title', 'description',)
```

**example/views.py**

```python
class CourseView(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
```

**example_search/urls.py**

```python
path('api/course/<int:pk>/', CourseView.as_view()),
```

**src/app/course.ts**

```javascript
export class Course {
  constructor(
    public id?: number,
    public course_code?: string,
    public title?: string,
    public description?: string
  ) {}
}
```

**src/app/course-search.service**

```javascript
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs/Rx';
import { Course } from './course';

@Injectable()
export class CourseSearchService {
  constructor(private httpClient: HttpClient) {}
  search(query: string): Observable<Course[]> {
    let url: string = 'http://localhost:8005/api/course/search/';
    const params: HttpParams = new HttpParams().set('query', query);
    return this.httpClient.get<Course[]>(url, {params});
  }
}
```

**src/app/course-search/course-search.component.ts**

```javascript
import { Component } from '@angular/core';
import { Course } from '../course';
import { CourseSearchService } from '../course-search.service';

@Component({
  selector: 'course-search',
  templateUrl: './course-search.component.html'
})
export class CourseSearchComponent {
  courses: Course[];
  constructor(private courseSearchService: CourseSearchService) {
    this.courses = [];
  }
  onSearch(query: string): void {
    this.courseSearchService.search(query).subscribe(courses => this.courses = courses);
  }
}
```

**src/app/course-search/course-search.component.html**

```html
<div class="container">
  <div class="row">
    <div class="col-lg-12">
      <h1 class="mt-4">Course Search</h1>
      <div class="input-group mt-3">
        <input class="form-control" type="text" placeholder="Enter text to search..." name="query"
          #query (keyup.enter)="onSearch(query.value)" (blur)="onSearch(query.value)"
        >
        <div class="input-group-append">
          <button class="btn btn-primary" type="button" (click)="onSearch(query.value)">Search</button>
        </div>
      </div>
      <ul class="list-group list-group-flush mt-3" *ngIf="courses.length > 0">
        <li class="list-group-item" *ngFor="let course of courses">
          <span class="font-weight-bold">{{ course.course_code }}</span> {{ course.title }}
        </li>
      </ul>
      <p class="mt-3" *ngIf="courses.length === 0">No results.</p>
    </div>
  </div>
</div>
```

**src/app/app.module.ts**

```javascript
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';
import { CourseSearchService } from './course-search.service';
import { AppComponent } from './app.component';
import { CourseSearchComponent } from './course-search/course-search.component';


@NgModule({
  declarations: [
    AppComponent,
    CourseSearchComponent
  ],
  imports: [
    HttpClientModule,
    BrowserModule,
    RouterModule.forRoot([
      { path: '', component: CourseSearchComponent }
    ]),
    FormsModule
  ],
  providers: [
    CourseSearchService
  ],
  bootstrap: [
    AppComponent
  ]
})
export class AppModule {}
```

## Course Detail

(Course detail here.)

**src/app/course-search.service**

```javascript
getCourse(id: number): Observable<Course> {
  let url: string = `http://localhost:8005/api/course/${id}/`;
  return this.httpClient.get<Course>(url);
}
```

**src/app/course/course.component.ts**

```javascript
import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { Course } from '../course';

@Component({
  selector: 'app-course',
  templateUrl: './course.component.html'
})
export class CourseComponent implements OnInit {
  course: Course;
  constructor(private route: ActivatedRoute) {}
  ngOnInit(): void {
    this.route.data.subscribe((data: {course: Course}) => this.course = data.course);
  }
}
```

**src/app/course/course.component.html**

```html
<div class="container">
  <div class="row">
    <div class="col-lg-12">
      <nav class="mt-4">
        <ol class="breadcrumb">
          <li class="breadcrumb-item">
            <a [routerLink]="['']">Search</a>
          </li>
          <li class="breadcrumb-item active">Detail</li>
        </ol>
      </nav>
      <h4 class="mt-3">
        <span class="font-weight-bold">{{ course.course_code }}</span> {{ course.title }}
      </h4>
      <p>{{ course.description }}</p>
    </div>
  </div>
</div>
```

**src/app/course.resolver.ts**

```javascript
import { Injectable } from '@angular/core';
import { ActivatedRouteSnapshot, Resolve, RouterStateSnapshot } from '@angular/router';
import { Observable } from 'rxjs/Rx';
import { Course } from './course';
import { CourseSearchService } from './course-search.service';

@Injectable()
export class CourseResolver implements Resolve<Course> {
  constructor(private courseSearchService: CourseSearchService) {}
  resolve(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<Course> {
    return this.courseSearchService.getCourse(route.params.id);
  }
}
```

**src/app/app.module.ts**

```javascript
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule } from '@angular/router';
import { CourseSearchService } from './course-search.service';
import { AppComponent } from './app.component';
import { CourseComponent } from './course/course.component';
import { CourseSearchComponent } from './course-search/course-search.component';
import { CourseResolver } from './course.resolver';


@NgModule({
  declarations: [
    AppComponent,
    CourseComponent,
    CourseSearchComponent
  ],
  imports: [
    HttpClientModule,
    BrowserModule,
    RouterModule.forRoot([
      { path: ':id', component: CourseComponent, resolve: { course: CourseResolver } },
      { path: '', component: CourseSearchComponent }
    ]),
    FormsModule
  ],
  providers: [
    CourseSearchService,
    CourseResolver
  ],
  bootstrap: [
    AppComponent
  ]
})
export class AppModule {}
```

**src/app/course-search/course-search.component.html**

```html
<li class="list-group-item" *ngFor="let course of courses" [routerLink]="['.', course.id]">
```

## Bridging the Gap

(Bridging the gap here.)

```
ng build -d /static
```