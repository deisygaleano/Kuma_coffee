from .auth_utils import es_admin, usuario_actual


def cuenta_usuario(request):
    usuario = usuario_actual(request)
    return {
        "usuario_actual": usuario,
        "usuario_es_admin": es_admin(usuario),
    }
