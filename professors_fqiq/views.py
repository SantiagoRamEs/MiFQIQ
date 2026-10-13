import logging
import secrets
import smtplib
import time

from django.contrib import messages
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
)
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import (
    GradeForm,
    InstitutionalEmailForm,
    ProfessorSuggestionForm,
    RegistrationDetailsForm,
)
from .models import Professor, Grade, ProfessorCourse, Course, StudentProfile
from django.db.models import Avg, Count

User = get_user_model()
logger = logging.getLogger(__name__)

REGISTRATION_CHALLENGE_KEY = "registration_challenge"
VERIFICATION_CODE_TTL = 600
VERIFICATION_MAX_ATTEMPTS = 5
VERIFICATION_RESEND_DELAY = 60


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
    if request.user.is_authenticated:
        return redirect("professors")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get("next", "")
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}
            ):
                return redirect(next_url)
            return redirect(settings.LOGIN_REDIRECT_URL)
        messages.error(request, "Nombre de usuario o contraseña incorrectos.")

    return render(
        request,
        "login.html",
        {"next": request.POST.get("next", request.GET.get("next", ""))},
    )


def register_view(request):
    challenge = request.session.get(REGISTRATION_CHALLENGE_KEY)
    step = "email"
    email_form = InstitutionalEmailForm()
    details_form = None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "send_code":
            email_form = InstitutionalEmailForm(request.POST)
            if email_form.is_valid():
                email = email_form.cleaned_data["email"]
                sent_at = challenge.get("sent_at", 0) if challenge else 0
                wait = VERIFICATION_RESEND_DELAY - (time.time() - sent_at)
                if wait > 0:
                    messages.error(
                        request,
                        f"Espera {int(wait) + 1} segundos antes de solicitar otro código.",
                    )
                    step = "email"
                else:
                    code = f"{secrets.randbelow(100000):05d}"
                    new_challenge = {
                        "email": email,
                        "code_hash": make_password(code),
                        "expires_at": time.time() + VERIFICATION_CODE_TTL,
                        "sent_at": time.time(),
                        "attempts": 0,
                        "verified": False,
                    }
                    try:
                        sent_count = send_mail(
                            "Código de verificación de Mi FQIQ",
                            (
                                f"Tu código de verificación es: {code}\n\n"
                                "Este código vence en 10 minutos. "
                                "Si no solicitaste crear una cuenta, ignora este mensaje."
                            ),
                            settings.DEFAULT_FROM_EMAIL,
                            [email],
                            fail_silently=False,
                        )
                    except (OSError, smtplib.SMTPException):
                        logger.exception("No se pudo enviar el código de registro.")
                        messages.error(
                            request,
                            "No se pudo enviar el correo. Inténtalo nuevamente más tarde.",
                        )
                    else:
                        if sent_count != 1:
                            logger.error(
                                "El backend de correo no confirmó el envío del código."
                            )
                            messages.error(
                                request,
                                "No se pudo confirmar el envío del correo. Inténtalo nuevamente.",
                            )
                        else:
                            request.session[REGISTRATION_CHALLENGE_KEY] = new_challenge
                            request.session.modified = True
                            challenge = new_challenge
                            step = "verify"
                            messages.success(
                                request, "Enviamos un código de 5 dígitos a tu correo."
                            )
            else:
                step = "email"

        elif action == "change_email":
            request.session.pop(REGISTRATION_CHALLENGE_KEY, None)
            challenge = None
            step = "email"

        elif action == "verify_code":
            step = "verify"
            challenge = request.session.get(REGISTRATION_CHALLENGE_KEY)
            if not challenge or challenge.get("verified"):
                request.session.pop(REGISTRATION_CHALLENGE_KEY, None)
                messages.error(request, "Solicita un nuevo código para continuar.")
                step = "email"
            elif time.time() > challenge["expires_at"]:
                request.session.pop(REGISTRATION_CHALLENGE_KEY, None)
                messages.error(request, "El código venció. Solicita uno nuevo.")
                step = "email"
            elif challenge["attempts"] >= VERIFICATION_MAX_ATTEMPTS:
                request.session.pop(REGISTRATION_CHALLENGE_KEY, None)
                messages.error(
                    request,
                    "Se agotaron los intentos. Solicita un nuevo código.",
                )
                step = "email"
            else:
                code = request.POST.get("code", "").strip()
                challenge["attempts"] += 1
                if len(code) == 5 and code.isdigit() and check_password(
                    code, challenge["code_hash"]
                ):
                    challenge["verified"] = True
                    challenge["verified_at"] = time.time()
                    request.session[REGISTRATION_CHALLENGE_KEY] = challenge
                    step = "details"
                    messages.success(request, "Correo verificado. Completa tus datos.")
                else:
                    if challenge["attempts"] >= VERIFICATION_MAX_ATTEMPTS:
                        request.session.pop(REGISTRATION_CHALLENGE_KEY, None)
                        messages.error(
                            request,
                            "Código incorrecto. Se agotaron los intentos; solicita otro.",
                        )
                        step = "email"
                    else:
                        request.session[REGISTRATION_CHALLENGE_KEY] = challenge
                        messages.error(request, "El código ingresado no es válido.")

        elif action == "create_account":
            challenge = request.session.get(REGISTRATION_CHALLENGE_KEY)
            if (
                not challenge
                or not challenge.get("verified")
                or time.time() > challenge.get("expires_at", 0)
            ):
                request.session.pop(REGISTRATION_CHALLENGE_KEY, None)
                messages.error(
                    request, "Verifica nuevamente tu correo antes de crear la cuenta."
                )
                step = "email"
            else:
                email = challenge["email"]
                username = email.split("@", 1)[0]
                user_for_validation = User(
                    username=username,
                    email=email,
                    first_name=request.POST.get("first_name", "").strip(),
                    last_name=request.POST.get("last_name", "").strip(),
                )
                details_form = RegistrationDetailsForm(
                    request.POST, user=user_for_validation
                )
                if details_form.is_valid():
                    try:
                        with transaction.atomic():
                            user = User.objects.create_user(
                                username=username,
                                email=email,
                                first_name=details_form.cleaned_data["first_name"],
                                last_name=details_form.cleaned_data["last_name"],
                                password=details_form.cleaned_data["password1"],
                            )
                            StudentProfile.objects.create(
                                user=user,
                                career=details_form.cleaned_data["career"],
                            )
                    except IntegrityError:
                        request.session.pop(REGISTRATION_CHALLENGE_KEY, None)
                        messages.error(
                            request,
                            "Ya existe una cuenta con este correo o nombre de usuario.",
                        )
                        step = "email"
                    else:
                        request.session.pop(REGISTRATION_CHALLENGE_KEY, None)
                        messages.success(
                            request, "Tu cuenta fue creada. Ya puedes iniciar sesión."
                        )
                        return redirect("login")
                else:
                    step = "details"

        else:
            messages.error(request, "La solicitud no es válida. Inténtalo nuevamente.")

    if (
        request.method == "GET"
        and step == "email"
        and challenge
        and challenge.get("verified")
    ):
        step = "details"
    elif (
        request.method == "GET"
        and step == "email"
        and challenge
        and not challenge.get("verified")
    ):
        if time.time() <= challenge.get("expires_at", 0):
            step = "verify"
        else:
            request.session.pop(REGISTRATION_CHALLENGE_KEY, None)
            challenge = None

    if step in {"verify", "details"}:
        if challenge:
            email_form = InstitutionalEmailForm(initial={"email": challenge["email"]})
    if step == "details" and details_form is None:
        challenge_email = challenge["email"] if challenge else ""
        details_form = RegistrationDetailsForm(
            user=User(
                username=challenge_email.split("@", 1)[0],
                email=challenge_email,
            )
        )

    return render(
        request,
        "register.html",
        {
            "step": step,
            "email_form": email_form,
            "details_form": details_form,
            "verified_email": challenge["email"] if challenge and challenge.get("verified") else "",
            "resend_wait": (
                max(
                    0,
                    int(
                        VERIFICATION_RESEND_DELAY
                        - (time.time() - challenge.get("sent_at", 0))
                    ),
                )
                if challenge and not challenge.get("verified")
                else 0
            ),
        },
    )

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
