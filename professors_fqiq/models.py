import os
import uuid

from django.conf import settings
from django.core.validators import MaxLengthValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Q

from .validators import validate_image_size, validate_image_format, validate_image_dimensions



import io

from django.core.files.base import ContentFile
from PIL import Image, ImageOps


def to_webp(uploaded, max_size=800, quality=80):
    uploaded.seek(0)
    img = Image.open(uploaded)
    img = ImageOps.exif_transpose(img)
    has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
    img = img.convert("RGBA" if has_alpha else "RGB")
    img.thumbnail((max_size, max_size), Image.LANCZOS)
    buffer = io.BytesIO()
    img.save(buffer, format="WEBP", quality=quality, method=6)
    return ContentFile(buffer.getvalue())

def professor_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    return f"professor_photos/{uuid.uuid4().hex}{ext}"



RATING_FIELDS = [
    "puntuality", "class_environment", "empathy", "class_evaluation",
    "exam_difficulty", "silabo", "grading_consistency", "teaching_material",
]


def rating_field():
    return models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )


class StudentProfile(models.Model):
    CAREER_CHOICES = [
        ("quimica", "Química"),
        ("ingenieria_quimica", "Ingeniería Química"),
        ("ingenieria_agua_tratamiento", "Ingeniería del Agua y Tecnologías de Tratamiento"),
        ("ingenieria_agroindustrial", "Ingeniería Agroindustrial"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    career = models.CharField(max_length=40, choices=CAREER_CHOICES)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_career_display()}"


class Course(models.Model):
    name_course = models.CharField(max_length=120)
    ciclo = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True,
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["ciclo", "name_course"]
        constraints = [
            models.UniqueConstraint(fields=["name_course", "ciclo"], name="unique_course_name_ciclo"),
        ]

    def __str__(self):
        return self.name_course


class ProfessorQuerySet(models.QuerySet):
    def with_averages(self):
        """Promedios en una sola consulta: Professor.objects.with_averages()"""
        return self.annotate(
            **{f"avg_{f}": Avg(f"coursestaught__grades__{f}") for f in RATING_FIELDS}
        )


class Professor(models.Model):
    name = models.CharField(max_length=100, unique=True)
    photo = models.ImageField(
        upload_to=professor_upload_path,
        blank=True,
        validators=[validate_image_size, validate_image_format, validate_image_dimensions],
    )
    created = models.DateTimeField(auto_now_add=True)

    objects = ProfessorQuerySet.as_manager()

    class Meta:
        verbose_name = "Profesor"
        verbose_name_plural = "Profesores"
        ordering = ["name"]

    def __str__(self):
        return self.name

    
    def save(self, *args, **kwargs):
        old_name = None
        if self.pk:
            old_name = (
                Professor.objects.filter(pk=self.pk)
                .values_list("photo", flat=True)
                .first()
            )

        if self.photo and not self.photo._committed:
            self.photo.save("photo.webp", to_webp(self.photo.file), save=False)

        super().save(*args, **kwargs)

        if old_name and old_name != self.photo.name:
            self.photo.storage.delete(old_name)

    def delete(self, *args, **kwargs):
        photo = self.photo
        super().delete(*args, **kwargs)
        if photo:
            photo.storage.delete(photo.name)
    
    
    def average_ratings(self):
        return Grade.objects.filter(professorcourse__professor=self).aggregate(
            **{f"avg_{f}": Avg(f) for f in RATING_FIELDS}
        )
    


class ProfessorCourse(models.Model):
    professor = models.ForeignKey(
        Professor, on_delete=models.CASCADE, related_name="coursestaught"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="professors"
    )

    class Meta:
        ordering = ["professor__name", "course__name_course"]
        constraints = [
            models.UniqueConstraint(fields=["professor", "course"], name="unique_professor_course"),
        ]

    def __str__(self):
        return f"{self.professor.name} - {self.course.name_course}"


class Grade(models.Model):
    professorcourse = models.ForeignKey(
        ProfessorCourse, on_delete=models.CASCADE, related_name="grades"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="grades",
    )

    puntuality = rating_field()
    class_environment = rating_field()
    empathy = rating_field()
    class_evaluation = rating_field()
    exam_difficulty = rating_field()
    silabo = rating_field()
    grading_consistency = rating_field()
    teaching_material = rating_field()

    comment = models.TextField(blank=True, validators=[MaxLengthValidator(1000)])

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
        ordering = ["-created"]
        constraints = [
            models.UniqueConstraint(
                fields=["professorcourse", "user"], name="unique_professorcourse_user"
            ),
            *[
                models.CheckConstraint(
                    condition=Q(**{f"{f}__range": (1, 5)}),  # en Django < 5.1 usa check=
                    name=f"grade_{f}_range_1_5",
                )
                for f in RATING_FIELDS
            ],
        ]

    def __str__(self):
        username = self.user.username if self.user else "Usuario eliminado"
        return f"{username} → {self.professorcourse}"