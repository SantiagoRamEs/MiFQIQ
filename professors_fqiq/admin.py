from django.contrib import admin
from .models import Professor, Grade, Course, ProfessorCourse, StudentProfile

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


class CourseAdmin(admin.ModelAdmin):
    search_fields = ["name_course"]
    readonly_fields = ("created",)


admin.site.register(Professor, ProfessorAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(StudentProfile)