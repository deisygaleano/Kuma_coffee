import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    def validate(self, password, user=None):
        requirements = [
            (r"[A-Z]", _("La contraseña debe incluir al menos una letra mayúscula.")),
            (r"[a-z]", _("La contraseña debe incluir al menos una letra minúscula.")),
            (r"\d", _("La contraseña debe incluir al menos un número.")),
            (r"[^A-Za-z0-9]", _("La contraseña debe incluir al menos un carácter especial.")),
        ]

        errors = [
            message
            for pattern, message in requirements
            if not re.search(pattern, password or "")
        ]
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Tu contraseña debe combinar mayúsculas, minúsculas, números y caracteres especiales."
        )
