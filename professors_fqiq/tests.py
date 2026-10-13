import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings

from .models import StudentProfile


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    SECURE_SSL_REDIRECT=False,
)
class AuthenticationViewsTests(TestCase):
    def setUp(self):
        self.User = get_user_model()

    def test_home_page_is_separate_from_login_form(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertContains(response, 'href="/login/"')
        self.assertContains(response, 'css/index.css')
        self.assertNotContains(response, 'name="password"')

    def test_login_page_has_its_own_template_and_stylesheet(self):
        response = self.client.get("/login/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "login.html")
        self.assertContains(response, 'css/login.css')
        self.assertContains(response, 'name="password"')

    def test_login_uses_username_and_password(self):
        self.User.objects.create_user(
            username="estudiante",
            email="estudiante@unmsm.edu.pe",
            password="Strong-password-482!",
        )

        response = self.client.post(
            "/login/",
            {"username": "estudiante", "password": "Strong-password-482!"},
        )

        self.assertRedirects(response, "/professors/")
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_registration_rejects_non_institutional_email(self):
        response = self.client.post(
            "/crear-cuenta/",
            {"action": "send_code", "email": "student@example.com"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "@unmsm.edu.pe")
        self.assertEqual(len(mail.outbox), 0)

    def test_registration_requires_verified_email_and_creates_profile(self):
        response = self.client.post(
            "/crear-cuenta/",
            {"action": "send_code", "email": "alumno123@unmsm.edu.pe"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        code_match = re.search(r"\b(\d{5})\b", mail.outbox[0].body)
        self.assertIsNotNone(code_match)
        code = code_match.group(1)

        response = self.client.post(
            "/crear-cuenta/",
            {"action": "verify_code", "code": code},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alumno123")
        self.assertContains(response, 'name="career"')

        response = self.client.post(
            "/crear-cuenta/",
            {
                "action": "create_account",
                "first_name": "Ana",
                "last_name": "Pérez",
                "career": "ingenieria_quimica",
                "password1": "Unrelated-Password-482!",
                "password2": "Unrelated-Password-482!",
            },
        )

        self.assertRedirects(response, "/login/")
        user = self.User.objects.get(username="alumno123")
        self.assertEqual(user.email, "alumno123@unmsm.edu.pe")
        self.assertEqual(user.first_name, "Ana")
        self.assertEqual(user.last_name, "Pérez")
        self.assertTrue(user.check_password("Unrelated-Password-482!"))
        self.assertEqual(
            user.student_profile.career,
            StudentProfile.CAREER_CHOICES[1][0],
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_registration_cannot_create_account_before_verification(self):
        response = self.client.post(
            "/crear-cuenta/",
            {
                "action": "create_account",
                "first_name": "Ana",
                "last_name": "Pérez",
                "career": "quimica",
                "password1": "Unrelated-Password-482!",
                "password2": "Unrelated-Password-482!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.User.objects.filter(username="alumno123").exists())

    def test_registration_rejects_an_incorrect_verification_code(self):
        self.client.post(
            "/crear-cuenta/",
            {"action": "send_code", "email": "alumno123@unmsm.edu.pe"},
        )
        sent_code = re.search(r"\b(\d{5})\b", mail.outbox[0].body).group(1)
        wrong_code = "00000" if sent_code != "00000" else "00001"

        response = self.client.post(
            "/crear-cuenta/",
            {"action": "verify_code", "code": wrong_code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no es válido")
        challenge = self.client.session["registration_challenge"]
        self.assertEqual(challenge["attempts"], 1)

    def test_existing_account_can_request_password_reset(self):
        self.User.objects.create_user(
            username="antiguo_usuario",
            email="antiguo@unmsm.edu.pe",
            password="Old-password-482!",
        )

        response = self.client.post(
            "/recuperar-contrasena/",
            {"email": "antiguo@unmsm.edu.pe"},
        )

        self.assertRedirects(response, "/recuperar-contrasena/enviado/")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("antiguo_usuario", mail.outbox[0].body)
