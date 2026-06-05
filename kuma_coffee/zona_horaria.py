import os
from pathlib import Path


def zona_horaria_local():
    """Resuelve la zona horaria del equipo o una variable de entorno."""
    configurada = os.environ.get("DJANGO_TIME_ZONE", "").strip()
    if configurada:
        return configurada

    try:
        enlace = Path("/etc/localtime").resolve()
        partes = enlace.parts
        if "zoneinfo" in partes:
            indice = partes.index("zoneinfo")
            return "/".join(partes[indice + 1 :])
    except OSError:
        pass

    return "America/Bogota"
