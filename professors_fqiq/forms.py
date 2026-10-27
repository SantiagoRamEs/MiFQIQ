from django import forms
from .models import Grade

CHOICES = [(i, str(i)) for i in range(0, 6)]


class GradeForm(forms.ModelForm):

    class Meta:
        model = Grade
        fields = ['puntuality', 'class_environment', 'empathy', 'class_evaluation', 'exam_difficulty', 'silabo',  'grading_consistency', 'teaching_material', 'comment']
        labels = {
            'professor': 'Profesor',
            'puntuality': 'Puntualidad',
            'class_environment': 'Ambiente de clase',
            'empathy': 'Empatía',
            'class_evaluation': 'Evalúa contenidos',
            'exam_difficulty': 'Accesibilidad de exámenes',
            'silabo': 'Cumple el sílabo',
            'grading_consistency':'Coherencia en la calif.',
            'teaching_material':'Material didáctico',
            'comment': 'Comentario',
        }
        widgets = {
            'puntuality': forms.Select(choices=CHOICES),
            'class_environment': forms.Select(choices=CHOICES),
            'empathy': forms.Select(choices=CHOICES),
            'class_evaluation': forms.Select(choices=CHOICES),
            'exam_difficulty': forms.Select(choices=CHOICES),
            'silabo': forms.Select(choices=CHOICES),
            'grading_consistency': forms.Select(choices=CHOICES),
            'teaching_material': forms.Select(choices=CHOICES),
        }

from django import forms

class ProfessorSuggestionForm(forms.Form):
    name = forms.CharField(max_length=100, label="Nombre completo (opcional) del profesor")
    photo = forms.ImageField(required=False, label="Fotografia del profesor (opcional)")
    course = forms.CharField(max_length=100, label="Cursos que dicta el profesor (los que conozcas)")
    comments = forms.CharField(widget=forms.Textarea, required=False, label="Comentarios (Escuela en la que dicta, teoria o laboratorio, etc)")