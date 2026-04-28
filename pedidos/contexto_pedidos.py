from .models import Pedido
from cuentas.models import Usuario


def carrito_cantidad(request):
    """Inyecta 'carrito_cantidad' en todos los templates."""
    try:
        usuario_id = request.session.get("usuario_id")
        if usuario_id:
            usuario = Usuario.objects.filter(pk=usuario_id).first()
        else:
            usuario = Usuario.objects.filter(correo="invitado@kuma.local").first()

        if not usuario:
            return {"carrito_cantidad": 0}

        pedido = Pedido.objects.filter(usuario=usuario, estado="borrador").first()
        if not pedido:
            return {"carrito_cantidad": 0}

        return {"carrito_cantidad": pedido.cantidad}
    except Exception:
        return {"carrito_cantidad": 0}