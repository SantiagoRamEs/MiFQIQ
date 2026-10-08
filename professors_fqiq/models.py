from django.conf import settings
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg
from .validators import validate_image_size, validate_image_format, validate_image_dimensions
from django.utils.text import slugify
import os

#Tabla de cursos
class Course(models.Model):

    name_course = models.CharField(max_length=120)

    ciclo = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank= True
        )

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ciclo', 'name_course']

    def __str__(self):
        return self.name_course
    
# Tabla de profesores
class Professor(models.Model):
    def professor_upload_path(instance, filename):
        name, ext = os.path.splitext(filename)
        safe_name = slugify(name)
        return f"professor_photos/{safe_name}{ext}"

    name = models.CharField(max_length=100)

    photo = models.ImageField(
        upload_to=professor_upload_path,
        blank=True,
        null=True,
        validators=[validate_image_size, validate_image_format, validate_image_dimensions]
        )
    
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professors'
        ordering = ['name']

    def __str__(self):
        return self.name

    #promedios
    def average_ratings(self):
        return Grade.objects.filter(professorcourse__professor=self).aggregate(
            avg_puntuality=Avg('puntuality'),
            avg_silabo=Avg('silabo'),
            avg_exam_difficulty=Avg('exam_difficulty'),
            avg_empathy=Avg('empathy'),
            avg_class_environment=Avg('class_environment'),
            avg_class_evaluation=Avg('class_evaluation'),
            avg_grading_consistency=Avg('grading_consistency'),
            avg_teaching_material=Avg('teaching_material'),
        )


class ProfessorCourse(models.Model):
    professor = models.ForeignKey(
        Professor,
        on_delete=models.CASCADE,
        related_name = 'coursestaught'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='professors',
    )

    class Meta:
        unique_together = ['professor', 'course']
        ordering = ['professor']

    def __str__(self):
        return f"{self.professor.name} - {self.course.name_course}"

# Tabla de calificaciones
class Grade(models.Model):
    professorcourse = models.ForeignKey(
        ProfessorCourse,
        on_delete=models.CASCADE,
        related_name='grades'
        )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='grades'
        )
    #items

    puntuality = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    class_environment = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    empathy = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    class_evaluation = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    exam_difficulty = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    silabo = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    grading_consistency = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    teaching_material = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    comment = models.TextField(blank = True)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Grade'
        verbose_name_plural = 'Grades'
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['professorcourse', 'user'], name='unique_professorcourse_user'
                )
        ]

    def __str__(self):
        username = self.user.username if self.user else 'Usuario eliminado'
        return f'{username} →  {self.professorcourse}'
