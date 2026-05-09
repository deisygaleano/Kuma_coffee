from .models import Usuario


ADMIN_ROLES = {"admin", "administrador", "superadmin"}


def usuario_actual(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return None
    return Usuario.objects.filter(pk=usuario_id).first()


def es_admin(usuario):
    return bool(usuario and (usuario.rol or "").strip().lower() in ADMIN_ROLES)


def usuario_es_admin(request):
    return es_admin(usuario_actual(request))
