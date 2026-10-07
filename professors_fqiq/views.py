from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, logout
from django import forms
from .forms import GradeForm
from .models import Professor, Grade, ProfessorCourse, Course
from django.db.models import Avg, Count
from .forms import ProfessorSuggestionForm
from django.core.mail import send_mail
from django.conf import settings
from allauth.socialaccount.models import SocialApp

User = get_user_model()


# Create your views here.
@login_required
def my_grades(request):

    grades = (
        Grade.objects
        .filter(user=request.user)
        .select_related(
            'professorcourse__professor',
            'professorcourse__course'
        )
        .order_by('-created')
    )

    return render(request, 'my_grades.html', {
        'grades': grades,
    })


@login_required
def custom_logout(request):
    logout(request)
    return redirect('/')

@login_required
def view_professors(request):

    rating_fields = [
        'puntuality',
        'class_environment',
        'empathy',
        'class_evaluation',
        'exam_difficulty',
        'silabo',
        'grading_consistency',
        'teaching_material',
    ]

    professors_qs = Professor.objects.annotate(
        **{f'avg_{f}': Avg(f'coursestaught__grades__{f}') for f in rating_fields}
    ).order_by('?')

    professors = []

    for prof in professors_qs:

        values = [
            getattr(prof, f'avg_{f}')
            for f in rating_fields
            if getattr(prof, f'avg_{f}') is not None
        ]

        general_avg = round(sum(values) / len(values), 1) if values else 0
        stars = '★' * max(0, min(int(round(general_avg)), 5))

        professors.append({
            'professor': prof,
            'general_avg': general_avg,
            'stars': stars,
        })

    return render(request, 'professors.html', {
        'professors': professors,
    })

def login_view(request):
    google_login_enabled = SocialApp.objects.filter(
        provider='google',
        sites__id=settings.SITE_ID,
    ).exists()
    return render(request, 'login.html', {
        'google_login_enabled': google_login_enabled,
    })

def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)

#CREAR UNA CALIFICACIÓN          
@login_required
def create_grade(request, pc_id):

    professor_course = get_object_or_404(ProfessorCourse, id=pc_id)
    professor = professor_course.professor

    # evitar que el usuario califique el mismo curso dos veces
    already_graded = Grade.objects.filter(
        professorcourse=professor_course,
        user=request.user
    ).exists()

    if already_graded:
        return redirect('profile_professor', pk=professor.id)

    if request.method == 'POST':
        form = GradeForm(request.POST)

        if form.is_valid():
            grade = form.save(commit=False)
            grade.user = request.user
            grade.professorcourse = professor_course
            grade.save()

            return redirect('profile_professor', pk=professor.id)

    else:
        form = GradeForm()

    return render(request, 'create_grade.html', {
        'form': form,
        'professor_course': professor_course,
        'professor': professor
    })



#PERFIL DE PROFESOR
@login_required
def profile_professor(request, pk):

    professor = get_object_or_404(Professor, pk=pk)

    rating_fields = [
        'puntuality',
        'class_environment',
        'empathy',
        'class_evaluation',
        'exam_difficulty',
        'silabo',
        'grading_consistency',
        'teaching_material',
    ]

    grades = Grade.objects.filter(professorcourse__professor=professor)

    # CURSOS OPTIMIZADOS
    courses_qs = ProfessorCourse.objects.filter(
        professor=professor
        ).select_related('course').annotate(
        total_grades=Count('grades'),

        avg_puntuality=Avg('grades__puntuality'),
        avg_class_environment=Avg('grades__class_environment'),
        avg_empathy=Avg('grades__empathy'),
        avg_class_evaluation=Avg('grades__class_evaluation'),
        avg_exam_difficulty=Avg('grades__exam_difficulty'),
        avg_silabo=Avg('grades__silabo'),
        avg_grading_consistency=Avg('grades__grading_consistency'),
        avg_teaching_material=Avg('grades__teaching_material'),
    )

    course_stats = []

    for pc in courses_qs:

        # obtener calificación del usuario (solo 1 query por curso)
        user_grade = None
        if request.user.is_authenticated:
            user_grade = Grade.objects.filter(
                user=request.user,
                professorcourse=pc
            ).only('id').first()

        data = {
            "pc": pc,
            "total_grades": pc.total_grades,

            "avg_puntuality": round(pc.avg_puntuality, 2) if pc.avg_puntuality else None,
            "avg_class_environment": round(pc.avg_class_environment, 2) if pc.avg_class_environment else None,
            "avg_empathy": round(pc.avg_empathy, 2) if pc.avg_empathy else None,
            "avg_class_evaluation": round(pc.avg_class_evaluation, 2) if pc.avg_class_evaluation else None,
            "avg_exam_difficulty": round(pc.avg_exam_difficulty, 2) if pc.avg_exam_difficulty else None,
            "avg_silabo": round(pc.avg_silabo, 2) if pc.avg_silabo else None,
            "avg_grading_consistency": round(pc.avg_grading_consistency, 2) if pc.avg_grading_consistency else None,
            "avg_teaching_material": round(pc.avg_teaching_material, 2) if pc.avg_teaching_material else None,

            "grade_id": user_grade.id if user_grade else None
        }

        course_stats.append(data)

    # COMENTARIOS
    grades_with_comments = grades.exclude(comment="")

    return render(request, "profile_professor.html", {
        "professor": professor,
        "courses": course_stats,
        "grades": grades_with_comments,
        "has_comments": grades_with_comments.exists()
    })

@login_required
def edit_grade(request, grade_id):

    grade = get_object_or_404(
        Grade,
        id=grade_id,
        user=request.user
    )

    professor = grade.professorcourse.professor
    course = grade.professorcourse.course

    if request.method == "POST":
        form = GradeForm(request.POST, instance=grade)

        if form.is_valid():
            form.save()
            return redirect('profile_professor', pk=professor.id)

    else:
        form = GradeForm(instance=grade)

    return render(request, 'edit_grade.html', {
        'form': form,
        'professor': professor,
        'course': course
    })

@login_required
def delete_grade(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id, user=request.user)

    if request.method == "POST":
        grade.delete()

    return redirect('my_grades')


def suggest_professor(request):
    if request.method == "POST":
        form = ProfessorSuggestionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            subject = "Nuevo profesor sugerido"
            message = f"""
            Nombre: {data['name']}
            Curso: {data['course']}
            Comentarios: {data['comments']}
            """

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ["ramirezsantiago2503@gmail.com"],  
                fail_silently=False,
            )

            return redirect("/professors/") 
    else:
        form = ProfessorSuggestionForm()

    return render(request, "suggest_professor.html", {"form": form})



#API
from rest_framework import viewsets
from .serializer import ProfessorSerializer, UserSerializer, GradeSerializer, ProfessorCourseSerializer, CourseSerializer

class ProfessorViewSet(viewsets.ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset =  User.objects.all()
    serializer_class = UserSerializer

class GradeViewSet(viewsets.ModelViewSet):
    queryset =  Grade.objects.all()
    serializer_class = GradeSerializer

class ProfessorCourseViewSet(viewsets.ModelViewSet):
    queryset =  ProfessorCourse.objects.all()
    serializer_class = ProfessorCourseSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset =  Course.objects.all()
    serializer_class = CourseSerializer

#
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

class DatosPrivadosView(APIView):
    # 1. Autenticación: ¿Quién eres? (Usa JWT)
    authentication_classes = [JWTAuthentication] 
    
    # 2. Permiso: ¿Tienes permiso de Admin?
    permission_classes = [IsAdminUser] 

    def get(self, request):
        # Si llega aquí, es porque es Admin y su JWT es válido
        return Response({
            "mensaje": f"Hola {request.user.username}, acceso concedido.",
            "data": "Información sensible de la facultad"
        })

