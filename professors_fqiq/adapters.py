from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.core.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages
import logging

class RestrictDomainSocialAccountAdapter(DefaultSocialAccountAdapter):

    

    def on_authentication_error(self, request, provider, error=None, exception=None, extra_context=None):
        logging.getLogger("allauth").error(
            "Auth error provider=%s error=%s exception=%r", provider, error, exception
        )
        return super().on_authentication_error(
            request, provider, error=error, exception=exception, extra_context=extra_context
        )

    def pre_social_login(self, request, sociallogin):
        allowed_domain = "unmsm.edu.pe"

        email = (sociallogin.user.email or "").strip().lower()

        if not email:
            email = (
                sociallogin.account.extra_data.get("email", "")
                .strip()
                .lower()
            )

        if not email:
            messages.error(
                request,
                "No se pudo obtener el correo desde Google."
            )
            raise ImmediateHttpResponse(redirect("login"))

        if not email.endswith(f"@{allowed_domain}"):
            messages.error(
                request,
                f"Debes iniciar sesión con un correo institucional "
                f"(usuario@{allowed_domain})"
            )
            raise ImmediateHttpResponse(redirect("login"))

        return super().pre_social_login(request, sociallogin)
    