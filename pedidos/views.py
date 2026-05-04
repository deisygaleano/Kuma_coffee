from urllib.parse import quote
from django.conf import settings
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogo.models import Producto
from cuentas.models import Usuario
from .models import LineaPedido, Pedido

def _usuario_actual(request):
    usuario_id = request.session.get("usuario_id")
    if usuario_id:
        usuario = Usuario.objects.filter(pk=usuario_id).first()
        if usuario:
            return usuario

    usuario, _ = Usuario.objects.get_or_create(
        correo="invitado@kuma.local",
        defaults={
            "nombre": "Cliente Invitado",
            "apellido": "",
            "telefono": "",
            "password": "pendiente_configurar_hash",
            "rol": "invitado",
        },
    )
    return usuario


def _pedido_borrador(usuario):
    pedido, _ = Pedido.objects.get_or_create(
        usuario=usuario,
        estado="borrador",
        defaults={"cantidad": 0, "valor": 0},
    )
    return pedido


def _recalcular_totales(pedido):
    agregados = pedido.lineas.aggregate(
        total_items=Coalesce(Sum("cantidad"), 0),
        total_valor=Coalesce(Sum(F("cantidad") * F("precio_unitario")), 0),
    )
    pedido.cantidad = agregados["total_items"]
    pedido.valor = agregados["total_valor"]
    pedido.save(update_fields=["cantidad", "valor"])


@require_POST
def agregar_al_carrito(request):
    producto_id = request.POST.get("producto_id")
    cantidad = int(request.POST.get("cantidad", 1))
    cantidad = max(1, cantidad)

    producto = get_object_or_404(Producto, pk=producto_id)
    usuario = _usuario_actual(request)
    pedido = _pedido_borrador(usuario)

    linea, creada = LineaPedido.objects.get_or_create(
        pedido=pedido,
        producto=producto,
        defaults={
            "cantidad": cantidad,
            "precio_unitario": producto.precio,
        },
    )
    if not creada:
        linea.cantidad += cantidad
        linea.precio_unitario = producto.precio
        linea.save(update_fields=["cantidad", "precio_unitario"])

    _recalcular_totales(pedido)
    return redirect(request.POST.get("next") or "pedidos:carrito")


def carrito(request):
    usuario = _usuario_actual(request)
    pedido = _pedido_borrador(usuario)
    lineas = pedido.lineas.select_related("producto", "producto__categoria")
    _recalcular_totales(pedido)
    whatsapp_url=_construir_url_whatsapp (lineas,pedido)
    return render(
        request,
        "carrito.html",
        {
            "pedido": pedido,
            "lineas": lineas,
            "whatsapp_url":whatsapp_url
        },
    )

@require_POST
def actualizar_cantidad(request, linea_id):
    usuario = _usuario_actual(request)
    pedido = _pedido_borrador(usuario)
    linea = get_object_or_404(LineaPedido, pk=linea_id, pedido=pedido)
    nueva_cantidad = int(request.POST.get("cantidad", 1))
    if nueva_cantidad < 1:
        nueva_cantidad = 1
    linea.cantidad = nueva_cantidad
    linea.save(update_fields=["cantidad"])
    _recalcular_totales(pedido)
    return redirect("pedidos:carrito")


@require_POST
def eliminar_linea(request, linea_id):
    usuario = _usuario_actual(request)
    pedido = _pedido_borrador(usuario)
    linea = get_object_or_404(LineaPedido, pk=linea_id, pedido=pedido)
    linea.delete()
    _recalcular_totales(pedido)
    return redirect("pedidos:carrito")

def _construir_url_whatsapp(lineas, pedido):
    numero = getattr(settings, "KUMA_WHATSAPP", "")
    if not numero or not lineas:
        return ""

    lineas_lista = list(lineas)
    items = "\n".join(
        f"  • {l.producto.nombre} x{l.cantidad} — ${l.subtotal:,}"
        for l in lineas_lista
    )
    mensaje = (
        "✅ *Kuma Coffee — Nuevo Pedido*\n\n"
        f"{items}\n\n"
        f"*Total: ${pedido.valor:,}*\n\n"
        "Por favor confirmar disponibilidad. ¡Gracias!"
    )
    return f"https://wa.me/{numero}?text={quote(mensaje)}"