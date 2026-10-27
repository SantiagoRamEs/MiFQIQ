from allauth.account.adapter import DefaultAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect

DOMINIO = "@unmsm.edu.pe"


class NoLocalSignupAccountAdapter(DefaultAccountAdapter):
    """Sin registro con usuario/contraseña: solo Google."""
    def is_open_for_signup(self, request):
        return False


class UNMSMSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True  # el registro social sí está permitido

    def pre_social_login(self, request, sociallogin):
        data = sociallogin.account.extra_data
        email = (data.get("email") or "").lower().strip()

        if not (email.endswith(DOMINIO) and data.get("email_verified", False)):
            messages.error(request, "Solo se permite el acceso con tu correo @unmsm.edu.pe.")
            raise ImmediateHttpResponse(redirect("home"))

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        messages.error(request, "No se pudo iniciar sesión con Google. Inténtalo de nuevo.")
        raise ImmediateHttpResponse(redirect("home"))