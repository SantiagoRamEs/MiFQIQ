from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Grade
from .models import StudentProfile

CHOICES = [(i, str(i)) for i in range(0, 6)]


class InstitutionalEmailForm(forms.Form):
    email = forms.EmailField(
        label="Correo institucional",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "placeholder": "usuario@unmsm.edu.pe",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if not email.endswith("@unmsm.edu.pe"):
            raise ValidationError("Usa tu correo institucional @unmsm.edu.pe.")

        username = email.split("@", 1)[0]
        User = get_user_model()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta con este correo.")
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(
                "El nombre de usuario asociado a este correo ya está registrado."
            )
        return email


class RegistrationDetailsForm(forms.Form):
    first_name = forms.CharField(
        label="Nombres",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "family-name"}),
    )
    career = forms.ChoiceField(
        label="Carrera",
        choices=StudentProfile.CAREER_CHOICES,
    )
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Las contraseñas no coinciden.")

        if password1 and self.user is not None:
            try:
                validate_password(password1, user=self.user)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned_data


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