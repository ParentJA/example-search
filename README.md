# Full Text Search with Django, PostgreSQL, and Angular (Part I)

(Intro here.)

Give users a list and they’re going to want to search it.

Implementing search in a web application isn't a new challenge, but as of Django 1.10 it's an easy one to overcome. Thanks to the `django.contrib.postgres.search` package, PostgreSQL search functions are abstracted into Python, which means you don't have to be a database guru to get started. 

(FIXME) In this tutorial, we'll demonstrate how to configure an app to use basic, full text, and fuzzy search.

Our application uses:
- Python (3.6.4)
- Django (2.0.1)
- Django REST Framework (3.7.7)
- PostgreSQL (9.6.3)

## Objectives

(Objectives here.)

## Project Setup

(Project setup here.)

Create a new Python virtual environment and install our dependencies with `pip`. We are using virtualenvwrapper.

```
computer$ mkvirtualenv example-search
(example-search) computer$ pip install django djangorestframework psycopg2
```

Create a new Django project and a Django app.

```
(example-search) computer$ django-admin startproject example_search
(example-search) computer$ cd example_search
(example-search) computer$ python manage.py startapp example
```

Create a new PostgreSQL user and database.

```
(example-search) computer$ createuser -d -e -W example_search
Password: password
CREATE ROLE example_search NOSUPERUSER CREATEDB NOCREATEROLE INHERIT LOGIN;
(example-search) computer$ createdb -e -O "example_search" example_search
CREATE DATABASE example_search OWNER example_search;
```

Open the Django settings file and replace the `DATABASES` attribute with the following code.

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

Note that we will pull our database configuration from environment variables. Create those environment variables in your terminal. If you are following along closely, the variables will match ours.

```
(example-search) computer$ export DB_NAME=example_search
(example-search) computer$ export DB_USER=example_search
(example-search) computer$ export DB_PASS=password
```

Back in the Django settings file, add `rest_framework` and `example` to `INSTALLED_APPS`. You app is ready to connect to the database.

Run the `migrate` command in your terminal to install the initial database tables.

```
(example-search) computer$ python manage.py migrate
(FIXME) Show sample output here.
```

Connect to the database and check that tables exist.

```
(example-search) computer$ psql -U example_search
example_search=# \dt
(FIXME) Show sample output here.
example_search=# \q
```

## App Foundation

Create a `Course` model. (FIXME: Why are we using courses?)

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

Create a database migration and migrate the database. If you're using the app, load the fixture data too.

```
(example-search) computer$ python manage.py makemigrations
Migrations for 'example':
  example/migrations/0001_initial.py
    - Create model Course
(example-search) computer$ python manage.py migrate
(example-search) computer$ python loaddata ./example/fixtures/courses.json
(example-search) computer$ psql -U example_search
example_search=# SELECT count(*) FROM example_course;
 count 
-------
   522
(1 row)

example_search=# \q
```

Create an admin page for the model.

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

Create a superuser.

```
(example-search) computer$ python manage.py createsuperuser
(FIXME: Show sample output.)
```

Run the app and take a look at the course data.

```
(example-search) computer$ python manage.py runserver 0.0.0.0:8000
```

Visit [http://localhost:8000/admin](http://localhost:8000/admin). Kill the app and continue.

Create the API. Make a serializer.

**example/serializers.py**

```python
from rest_framework import serializers
from .models import Course


class CourseSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'course_code', 'title',)
```

Create a view. For now, make the API return all courses or none.

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

Connect the view to a URL path.

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

A basic search matches your query to the value of a field. The database compares the characters at each position and they must be exactly the same. If you search for “biology” then your query will match “biology” but not “BIOLOGY” or “animal biology”.

In many cases, finding a perfect match is imperative. When you need to retrieve a record identified by a username or a natural key, finding a close match isn’t good enough. Who snagged the last available seat—_student25_ or _student26_? You better get it right or the consequences can be disastrous.

Modify the view to fetch courses whose fields match the query.

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

The Django `QuerySet` makes the equivalent SQL query.

```sql
SELECT id, course_code, title
  FROM example_course
 WHERE course_code = 'Animal Biology' 
    OR title = 'Animal Biology' 
    OR description = 'Animal Biology';
```

Here's how it looks when run in `psql`.

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

When the stakes are low, full text search gives users the ability to find data that sort of matches. Many times, when users search “biology”, they want to see “BIOLOGY” and “animal biology” too. They also want to see “biological”. The results should be related to the query instead of an exact match.

Full text search works by breaking down the query and the target into tokens. A token is a word and most engines eliminate stop words like “a” and “the” because they are so common. PostgreSQL maps these tokens to positions in the document and searches this dictionary for matching tokens. “Biology” and “biological” share the same root and are considered a match.

A basic search works fine when your query matches a field's value exactly, but what about when your query matches part of the value? You might point to the `contains` lookup expression. But wouldn't it be nice if when you searched for "biology", your query matched "biological" too?

Modify the view to perform full text search on all of the fields.

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

The following SQL will return equivalent results.

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

(What do each of the functions do?)

Here's how the query runs in `psql`.

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

(Talk about results. Why do Lifespan Development, Developmental Pyschology, and Soil Science appear before Cancer Biology?)

## Ranking

(Ranking here.)

Look at the previous example. We searched for "biology" but we see "Soil Science" above "Cancer Biology". This is a ranking issue. We got the correct results but they're not in the correct order.

Modify the view code to use ranking. 

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

(What do the weights do? What is the significance of the value?)

Equivalent SQL.

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

Run in `psql`. (Talk about results vis-a-vis ranking.)

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

We've been calculating the `vector` in each query. We can optimize this query by precalculating the vector and storing it in the `example_course` database as a field.

Modify the `Course` model to use the `SearchVectorField`. (Talk about pre-processing the search vector and how it improves performance.)

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

Make migrations.

```
python manage.py makemigrations
```

Add a data migration operation to update all of the course data.

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

Run the migration.

```
python manage.py migrate
```

Add a signal to update the search vector everytime a course changes.

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

Modify the following files to finish setting up the signal.

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

Add `search_vector` to the `fields` and `readonly_fields` of the `CourseAdmin`. Making this change will let you see the vector in the admin page.

## Fuzzy Search

(Fuzzy search here.)

Full text search works well when your search term is spelled correctly. We still want to find results when a user mistypes a word. (How do trigrams work?)

Add the `pg_trgm` extension to the database.

```
(example-search) computer$ psql -U example_search
example_search=# CREATE EXTENSION pg_trgm;
CREATE EXTENSION
example_search=# SELECT show_trgm('hello');
            show_trgm            
---------------------------------
 {"  h"," he",ell,hel,llo,"lo "}
(1 row)

example_search=# \q
```

Modify the view to use fuzzy search.

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

Here is the SQL equivalent.

```sql
SELECT id, course_code, title, similarity(title, 'bilogy') AS similarity
  FROM example_course
 WHERE similarity(title, 'bilogy') >= 0.3
 ORDER BY similarity DESC;
```

An example in `psql`.

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

Modify the view to include a lot of code. (Why are we making these choices? Are we using what we learned? Talk about rank.)

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

SQL equivalent.

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

Final example in `psql`.

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

Add scripts and styles.

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

Modify the base component.

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

Replace the contents with `<router-outlet>` to set up routing.

**src/app/app.component.htmlts**

```html
<router-outlet></router-outlet>
```

## Course Search

(Course search here.)

Create a `Course` model for the client.

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

Create a course search service.

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
    let url: string = '/api/course/search/';
    const params: HttpParams = new HttpParams().set('query', query);
    return this.httpClient.get<Course[]>(url, {params});
  }
}
```

And a component.

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

The template should have a search field and button. Searching returns a list of courses.

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

Modify the app module file to support all of the changes.

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

Course search doesn't return descriptions. Need new API to return full course detail.

Create a serializer.

**example/serializers.py**

```python
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'course_code', 'title', 'description',)
```

Create a view.

**example/views.py**

```python
class CourseView(RetrieveAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
```

Connect the view to a URL path.

**example_search/urls.py**

```python
path('api/course/<int:pk>/', CourseView.as_view()),
```

Add course detail function to the course search service.

**src/app/course-search.service**

```javascript
getCourse(id: number): Observable<Course> {
  let url: string = `/api/course/${id}/`;
  return this.httpClient.get<Course>(url);
}
```

Create a component.

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

And a simple template.

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

Create a resolver to load the course detail when the course tile is clicked.

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

Update app module once more.

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

Final step to activate routing.

**src/app/course-search/course-search.component.html**

```html
<li class="list-group-item" *ngFor="let course of courses" [routerLink]="['.', course.id]">
```

## Bridging the Gap

(Bridging the gap here.)

Make some final changes to the settings to use the Angular code.

**example_search/settings.py**

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'www/example-search/dist')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'www/example-search/dist')
]
```

Run this code to build the client for Django to use.

```
ng build -d /static
```