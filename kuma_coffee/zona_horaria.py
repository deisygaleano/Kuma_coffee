import os
from datetime import datetime
from pathlib import Path


def zona_horaria_local():
    """Resuelve la zona horaria del equipo o una variable de entorno."""
    configurada = os.environ.get("DJANGO_TIME_ZONE", "").strip()
    if configurada:
        return configurada

    try:
        tzinfo = datetime.now().astimezone().tzinfo
        nombre = getattr(tzinfo, "key", None)
        if nombre:
            return nombre
    except (OSError, ValueError, AttributeError):
        pass

    try:
        enlace = Path("/etc/localtime").resolve()
        partes = enlace.parts
        if "zoneinfo" in partes:
            indice = partes.index("zoneinfo")
            return "/".join(partes[indice + 1 :])
    except OSError:
        pass

    return "America/Bogota"


def ahora_local():
    """Fecha y hora del sistema donde corre Django."""
    from django.conf import settings
    from django.utils import timezone

    if settings.USE_TZ:
        return timezone.now()
    return datetime.now()
