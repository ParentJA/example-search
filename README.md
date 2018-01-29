# Full Text Search with Django, PostgreSQL, and Angular (Part I)

(Intro here.)

## Objectives

(Objectives here.)

## Project Setup

(Project setup here.)

```
pip install django djangorestframework
```

## Basic Search

(Basic search here.)

## Full Text Search

(Full text search here.)

## Optimization

(Optimization here.)

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