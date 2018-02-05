# Full Text Search with Django, PostgreSQL, and Angular (Part I)

Implementing search in a web application isn't a new challenge, but as of Django 1.10 it's an easy one to overcome. Thanks to the `django.contrib.postgres.search` package, PostgreSQL text search functions are abstracted into Python, which means you don't have to be a database guru to get started.

In this tutorial, we'll review how Django typically finds records in the database. Then we'll introduce _full text search_ and demonstrate how to perform it using Django.

## Objectives

By the end of this tutorial, you should:
- Have a basic understanding of full text search
- Know how to implement full text search using Django and PostgreSQL

## Project Setup

Our application uses:
- Python (3.6.4)
- Django (2.0.1)
- Django REST Framework (3.7.7)
- PostgreSQL (9.6.3)

Open your terminal and create a new PostgreSQL user and database. Enter a password when prompted.

```
computer$ createuser -d -e -s -W example_search
Password: pAssw0rd!
CREATE ROLE example_search SUPERUSER CREATEDB CREATEROLE INHERIT LOGIN;
computer$ createdb -e -O "example_search" -W example_search
Password: pAssw0rd!
CREATE DATABASE example_search OWNER example_search;
```

Export environment variables for your new database name, user, and password.

```
computer$ export DB_NAME=example_search DB_USER=example_search DB_PASS=pAssw0rd!
```

Make a new Python virtual environment and install the project dependencies with `pip`. (We are using [virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/).)

```
computer$ mkvirtualenv example-search
(example-search) computer$ pip install django djangorestframework psycopg2
```

Start a new Django project and a Django app.

```
(example-search) computer$ django-admin startproject example_search
(example-search) computer$ cd example_search
(example-search) computer$ python manage.py startapp example
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

Note that our database settings use the environment variables we configured in a previous step. Our app is ready to connect to the database.

Add `rest_framework` and `example` to `INSTALLED_APPS`. 

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'example',
]
```

Run the `python manage.py migrate` command in your terminal to install the initial database tables. You should see the following output.

```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying sessions.0001_initial... OK
```

Open a new terminal window (or tab). Connect to the database with `psql` and confirm that the tables exist.

```
(example-search) computer$ psql -U example_search
example_search=# \c example_search
example_search=# \dt
                      List of relations
 Schema |            Name            | Type  |     Owner      
--------+----------------------------+-------+----------------
 public | auth_group                 | table | example_search
 public | auth_group_permissions     | table | example_search
 public | auth_permission            | table | example_search
 public | auth_user                  | table | example_search
 public | auth_user_groups           | table | example_search
 public | auth_user_user_permissions | table | example_search
 public | django_admin_log           | table | example_search
 public | django_content_type        | table | example_search
 public | django_migrations          | table | example_search
 public | django_session             | table | example_search
(10 rows)
```

Now we're ready to write some code.

## App Foundation

Throughout this tutorial, we're going to work with the concept of a college course. Everyone who attended college remembers perusing the course catalog before registration. Whether you thumbed through a paper booklet or scrolled through pages of text on a computer, finding the course you wanted wasn't easy. A course catalog is the perfect candidate for full text search.

Start by creating a `Course` model.

**example/models.py**

```python
from django.db import models


class Course(models.Model):
    """A course offered at a university."""
    course_code = models.CharField(max_length=16, unique=True)
    title = models.CharField(max_length=250)
    description = models.TextField()

    def __str__(self):
        return f'{self.course_code} {self.title}'
```

Make a database migration and migrate the database.

```
(example-search) computer$ python manage.py makemigrations
Migrations for 'example':
  example/migrations/0001_initial.py
    - Create model Course
(example-search) computer$ python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, example, sessions
Running migrations:
  Applying example.0001_initial... OK
```

If you've downloaded the example code, then load the fixture data too.

```
(example-search) computer$ python manage.py loaddata ./example/fixtures/courses.json
Installed 522 object(s) from 1 fixture(s)
```

You can confirm the updates to the database in `psql` if you want.

```
example_search=# SELECT count(*) FROM example_course;
 count 
-------
   522
(1 row)
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
Username (leave blank to use 'computer'): admin
Email address: admin@example.com
Password: pAssw0rd!
Password (again): pAssw0rd!
Superuser created successfully.
```

Start the app server.

```
(example-search) computer$ python manage.py runserver 0.0.0.0:8000
```

Visit [http://localhost:8000/admin](http://localhost:8000/admin) to view the course data in the admin page.

Next, create the course search API. Start with a serializer.

**example/serializers.py**

```python
from rest_framework import serializers
from .models import Course


class CourseSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'course_code', 'title',)
```

Create a view. For now, make the API return nothing.

**example/views.py**

```python
from rest_framework.generics import ListAPIView
from .models import Course
from .serializers import CourseSearchSerializer


class CourseSearchView(ListAPIView):
    serializer_class = CourseSearchSerializer

    def get_queryset(self):
        return Course.objects.none()
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

Did everything work? Hit the API with `curl` to find out.

```
computer$ curl http://localhost:8005/api/course/search/
[]
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

```
 id | course_code | title 
----+-------------+-------
(0 rows)
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
 id  | course_code |     title      
-----+-------------+----------------
 459 | BIOL221     | Animal Biology
(1 row)
```

## Full Text Search

(FIXME: With full text search, the stakes are lower than with basic search, and the criteria for matching is looser.)

Whereas basic search compares the characters at each position in a query to those in a document, full text search takes a different approach. The database breaks a document and a query into smaller parts, and then it transforms those parts using a list of rules. An example of a rule is: convert a word to its root. The database finds all of the documents that contain the same parts as the query and returns them in the search results.

### PostgreSQL

PostgreSQL starts the process by parsing a document into a list of strings, or _tokens_. It parses most English words as tokens by removing whitespace and punctuation. The sentence, _I called my mother to say "hi"._, consists of these tokens: `I`, `called`, `my`, `mother`, `to`, `say`, `hi`.

The next step involves converting the tokens into _lexemes_. A lexeme is the shortest version of a word that still has meaning. Most of the time, the conversion simply reduces a word to its root. During this step, PostgreSQL also changes all upper-case characters to lower-case and eliminates common words like "a" and "the". This procedure is known as _normalization_.

As a final step, PostgreSQL creates an index for each lexeme by mapping it to its position in the original document. Here's the result of calling the `to_tsvector()` function, which PostgreSQL uses to prepare documents for text search, on our example.

```sql
SELECT to_tsvector('I called my mother to say "hi".');
```

```psql
            to_tsvector             
------------------------------------
 'call':2 'hi':7 'mother':4 'say':6
(1 row)
```

The function returns an instance of the `tsvector` data type. Take note of a few things. 
1. PostgreSQL removes the common words "I", "my", and "to". 
2. It reduces the word "called" to its root "call". 
3. It maps the lexemes to their locations in the document, starting with the position 1. (See the table below.)

| Position | Token | Lexeme |
| -------- | ----- | ------ |
| 1 | I | (eliminated) |
| 2 | called | call |
| 3 | my | (eliminated) |
| 4 | mother | mother |
| 5 | to | (eliminated) |
| 6 | say | say |
| 7 | hi | hi |

PostgreSQL normalizes a query using a similar process. In this case, it calls the `to_tsquery()` function to produce a `tsquery` object. The `tsquery` object is complementary to `tsvector`, but it's not the same. For more information, check out the official [PostgreSQL text search documentation](https://www.postgresql.org/docs/9.6/static/textsearch-intro.html).

```sql
SELECT to_tsquery('calling');
```

```psql
 to_tsquery 
------------
 'call'
(1 row)
```

PostgreSQL performs the actual search by checking if the document and the query share common lexemes. The "calling" query matches our document because both objects include the lexeme "call". 

```sql
SELECT to_tsvector('I called my mother to say "hi".') @@ to_tsquery('calling');
```

```psql
 ?column? 
----------
 t
(1 row)
```

### Django

Django abstracts the `to_tsvector()` PostgreSQL function to the `SearchVector` Python class and `to_tsquery()` to `SearchQuery`. 

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

This example introduces two new Django classes--`SearchVector` and `SearchQuery`. Using `SearchVector` invokes the `to_tsvector()` function in PostgreSQL. The process of normalization follows these general steps:
1. The text is broken into words and punctuation is discarded. These words are known as tokens.
2. The tokens are converted to their roots in a process known as stemming. For example, the word "programming" would be converted to the root "program".

The process of normalization always produces the same results on the same input. The `to_tsvector()` function maps the roots to their position in the text (indexed for rapid searching).

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
(example-search) computer$ python manage.py makemigrations
Migrations for 'example':
  example/migrations/0002_course_search_vector.py
    - Add field search_vector to course
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
(example-search) computer$ python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, example, sessions
Running migrations:
  Applying example.0002_course_search_vector... OK
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
example_search=# \c example_search
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
        ).filter(similarity__gte=0.3).order_by('-similarity')
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
(example-search) computer$ mkdir www && cd www
(example-search) computer$ ng new example-search
(example-search) computer$ cd example-search
(example-search) computer$ npm install --save bootstrap@4.0.0 bootswatch@4.0.0 jquery@3.3.1 popper.js@1.12.9
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

```
(example-search) computer$ ng generate class course
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

Create a course search service.

```
(example-search) computer$ ng generate service course-search
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
    let url: string = '/api/course/search/';
    const params: HttpParams = new HttpParams().set('query', query);
    return this.httpClient.get<Course[]>(url, {params});
  }
}
```

And a component.

```
(example-search) computer$ ng generate component course-search
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

```
(example-search) computer$ ng generate component course
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

```
(example-search) computer$ ng generate service resolver
```

Rename files to `course.resolver`.

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
      { path: 'course/:id', component: CourseComponent, resolve: { course: CourseResolver } },
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
<li class="list-group-item" *ngFor="let course of courses" [routerLink]="['/course', course.id]">
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

```python
from django.contrib import admin
from django.urls import path
from django.views.generic.base import TemplateView
from example.views import CourseSearchView, CourseView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/course/search/', CourseSearchView.as_view()),
    path('api/course/<int:pk>/', CourseView.as_view()),
    path('', TemplateView.as_view(template_name='index.html')),
]
```

Run this code to build the client for Django to use.

```
ng build -d /static
```