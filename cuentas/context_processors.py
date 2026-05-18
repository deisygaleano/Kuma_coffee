from .auth_utils import es_admin, usuario_actual


def _iniciales_usuario(usuario):
    if not usuario:
        return ""

    partes_nombre = [
        (usuario.nombre or "").strip(),
        (usuario.apellido or "").strip(),
    ]
    iniciales = "".join(parte[0] for parte in partes_nombre if parte)

    if iniciales:
        return iniciales[:2].upper()

    correo = (usuario.correo or "").strip()
    return correo[:2].upper()


def cuenta_usuario(request):
    usuario = usuario_actual(request)
    return {
        "usuario_actual": usuario,
        "usuario_iniciales": _iniciales_usuario(usuario),
        "usuario_es_admin": es_admin(usuario),
    }
