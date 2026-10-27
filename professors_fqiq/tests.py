from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model


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
