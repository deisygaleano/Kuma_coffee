import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    def validate(self, password, user=None):
        requirements = [
            (r"[A-Z]", _("La contrasena debe incluir al menos una letra mayuscula.")),
            (r"[a-z]", _("La contrasena debe incluir al menos una letra minuscula.")),
            (r"\d", _("La contrasena debe incluir al menos un numero.")),
            (r"[^A-Za-z0-9]", _("La contrasena debe incluir al menos un caracter especial.")),
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
            "Tu contrasena debe combinar mayusculas, minusculas, numeros y caracteres especiales."
        )
