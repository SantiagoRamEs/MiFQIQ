from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from .models import Course, CourseCareer, Grade, Professor, ProfessorCourse, StudentProfile


@override_settings(
    SECURE_SSL_REDIRECT=False,
)
class AuthenticationViewsTests(TestCase):
    def test_home_page_renders_login_link_without_google_app_configuration(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Iniciar sesión con Google")
        self.assertContains(response, 'href="/accounts/google/login/"')
        self.assertNotContains(response, "<form")
        self.assertNotContains(response, 'href="/login/"')
        self.assertNotContains(response, "Crear cuenta")

    def test_authentication_routes_are_removed(self):
        for path in ("/login/", "/accounts/login/", "/accounts/google/login/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_logout_requires_post(self):
        user = get_user_model().objects.create_user(username="logout-user")
        self.client.force_login(user)

        response = self.client.get("/logout/")

        self.assertEqual(response.status_code, 405)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_logout_clears_session_and_returns_home(self):
        user = get_user_model().objects.create_user(username="logout-user")
        self.client.force_login(user)

        response = self.client.post("/logout/")

        self.assertRedirects(response, "/", fetch_redirect_response=False)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_password_and_code_registration_routes_are_removed(self):
        for path in (
            "/crear-cuenta/",
            "/recuperar-contrasena/",
            "/restablecer-contrasena/abc/token/",
            "/api/token/",
            "/api/token/refresh/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_login_required_remains_on_protected_views(self):
        response = self.client.get("/professors/")

        self.assertRedirects(
            response,
            "/accounts/login/?next=/professors/",
            fetch_redirect_response=False,
        )


@override_settings(SECURE_SSL_REDIRECT=False)
class CareerCourseAccessTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="chemistry-student")
        self.profile = StudentProfile.objects.create(
            user=self.user, career="quimica"
        )
        self.professor = Professor.objects.create(name="Docente de prueba")
        self.chemistry_course = Course.objects.create(name_course="Curso de química")
        self.other_course = Course.objects.create(name_course="Curso de otra carrera")
        self.unassigned_course = Course.objects.create(name_course="Curso sin asignar")
        CourseCareer.objects.create(course=self.chemistry_course, career="quimica")
        CourseCareer.objects.create(
            course=self.other_course, career="ingenieria_quimica"
        )
        self.chemistry_pc = ProfessorCourse.objects.create(
            professor=self.professor, course=self.chemistry_course
        )
        self.other_pc = ProfessorCourse.objects.create(
            professor=self.professor, course=self.other_course
        )
        self.unassigned_pc = ProfessorCourse.objects.create(
            professor=self.professor, course=self.unassigned_course
        )
        self.client.force_login(self.user)

    def create_grade(self, professor_course, user, comment="Comentario de prueba"):
        return Grade.objects.create(
            professorcourse=professor_course,
            user=user,
            puntuality=4,
            class_environment=4,
            empathy=4,
            class_evaluation=4,
            exam_difficulty=4,
            silabo=4,
            grading_consistency=4,
            teaching_material=4,
            comment=comment,
        )

    def test_for_career_includes_matching_and_unassigned_courses(self):
        courses = set(Course.objects.for_career("quimica"))

        self.assertEqual(
            courses, {self.chemistry_course, self.unassigned_course}
        )

    def test_professor_profile_lists_only_matching_and_unassigned_courses(self):
        response = self.client.get(
            "/professors/{}/".format(self.professor.pk)
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.chemistry_course.name_course)
        self.assertContains(response, self.unassigned_course.name_course)
        self.assertNotContains(response, self.other_course.name_course)

    def test_professor_list_shows_only_matching_and_unassigned_courses(self):
        response = self.client.get("/professors/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.chemistry_course.name_course)
        self.assertContains(response, self.unassigned_course.name_course)
        self.assertNotContains(response, self.other_course.name_course)

    def test_create_grade_rejects_course_assigned_to_another_career(self):
        response = self.client.get(
            "/grade/create/{}/".format(self.other_pc.pk)
        )

        self.assertEqual(response.status_code, 403)

    def test_create_grade_allows_matching_course(self):
        response = self.client.get(
            "/grade/create/{}/".format(self.chemistry_pc.pk)
        )

        self.assertEqual(response.status_code, 200)

    def test_missing_student_profile_redirects_to_completion(self):
        for user in (
            get_user_model().objects.create_user(username="no-student-profile"),
            get_user_model().objects.create_user(
                username="staff-without-profile", is_staff=True
            ),
        ):
            self.client.force_login(user)
            for path in (
                "/professors/",
                "/professors/{}/".format(self.professor.pk),
                "/grade/create/{}/".format(self.chemistry_pc.pk),
            ):
                with self.subTest(user=user.username, path=path):
                    response = self.client.get(path)
                    self.assertRedirects(
                        response,
                        "/completar-perfil/",
                        fetch_redirect_response=False,
                    )

    def test_comment_shows_author_career_and_handles_missing_author_profile(self):
        self.create_grade(self.chemistry_pc, self.user)
        user_without_profile = get_user_model().objects.create_user(
            username="author-without-profile"
        )
        self.create_grade(self.other_pc, user_without_profile)
        self.create_grade(self.unassigned_pc, None, comment="Comentario anónimo")

        response = self.client.get(
            "/professors/{}/".format(self.professor.pk)
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Química")
        self.assertContains(response, "Comentario anónimo")
        self.assertContains(response, "Usuario eliminado")
        self.assertNotContains(response, "author-without-profile")

    def test_comment_uses_the_career_choice_display_label(self):
        self.create_grade(self.chemistry_pc, self.user)
        self.profile.career = "ingenieria_agua_tratamiento"
        self.profile.save(update_fields=["career"])

        response = self.client.get(
            "/professors/{}/".format(self.professor.pk)
        )

        self.assertContains(response, "Ingeniería del Agua y TT")
        self.assertNotContains(
            response, "Ingeniería del Agua y Tecnologías de Tratamiento"
        )

    def test_staff_with_profile_can_see_all_courses(self):
        staff_user = get_user_model().objects.create_user(
            username="staff-user", is_staff=True
        )
        StudentProfile.objects.create(user=staff_user, career="quimica")
        self.client.force_login(staff_user)

        response = self.client.get(
            "/professors/{}/".format(self.professor.pk)
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.other_course.name_course)
