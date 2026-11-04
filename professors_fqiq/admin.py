from django.contrib import admin

from .models import (
    Course,
    CourseCareer,
    Grade,
    Professor,
    ProfessorCourse,
    StudentProfile,
)

class ProfessorCourseInline(admin.TabularInline):
    model = ProfessorCourse
    extra = 1
    autocomplete_fields = ["course"]

class ProfessorAdmin(admin.ModelAdmin):
    inlines = [ProfessorCourseInline]
    list_display = ("name", "get_courses")
    readonly_fields = ("created",)
    
    def get_courses(self, obj):
        return ", ".join(pc.course.name_course for pc in obj.coursestaught.all())

    get_courses.short_description = "Cursos"



class GradeAdmin(admin.ModelAdmin):
    readonly_fields = ("created",)


class CourseCareerInline(admin.TabularInline):
    model = CourseCareer
    extra = 1


class CourseAdmin(admin.ModelAdmin):
    search_fields = ["name_course"]
    readonly_fields = ("created",)
    inlines = [CourseCareerInline]
    list_filter = ("careers__career",)


admin.site.register(Professor, ProfessorAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(StudentProfile)