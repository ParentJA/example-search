# Full Text Search with Django, PostgreSQL, and Angular (Part I)

(Intro here.)

## Objectives

(Objectives here.)

## Project Setup

(Project setup here.)

```
pip install django djangorestframework
createdb example_search
```

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
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
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

```sql
SELECT *
  FROM example_course;
```

## Basic Search

(Basic search here.)

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
        return Course.objects.filter(title__iexact=query)
```

```sql
SELECT *
  FROM example_course
 WHERE UPPER(title) = UPPER('biology');
```

## Full Text Search

(Full text search here.)

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

## Ranking

(Ranking here.)

## Fuzzy Search

(Fuzzy search here.)

## Putting It All Together

(Putting it all together here.)

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