from urllib.parse import quote, urlencode
from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from catalogo.inventario import StockInsuficienteError, descontar_stock_lineas, stock_disponible
from catalogo.models import Producto
from cuentas.models import Usuario
from cuentas.auth_utils import es_admin
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


def _redirect_tras_rechazo_carrito_admin(request):
    next_url = request.POST.get("next") or reverse("catalogo:lista")
    messages.error(request, "Los administradores no pueden agregar productos al carrito.")
    return redirect(next_url)


@require_POST
def agregar_al_carrito(request):
    if not request.session.get("usuario_id"):
        next_url = request.POST.get("next") or reverse("catalogo:lista")
        login_url = f"{reverse('cuentas:login')}?{urlencode({'next': next_url})}"
        messages.error(
            request,
            "Para agregar productos al carrito debes iniciar sesión.",
            extra_tags="auth",
        )
        return redirect(login_url)

    usuario = _usuario_actual(request)
    if es_admin(usuario):
        return _redirect_tras_rechazo_carrito_admin(request)

    producto_id = request.POST.get("producto_id")
    cantidad = int(request.POST.get("cantidad", 1))
    cantidad = max(1, cantidad)

    producto = get_object_or_404(
        Producto.objects.select_related("inventario"),
        pk=producto_id,
    )
    disponible = stock_disponible(producto)
    if disponible == 0:
        messages.error(request, f"«{producto.nombre}» está agotado y no se puede añadir al carrito.")
        next_url = request.POST.get("next") or reverse("catalogo:lista")
        return redirect(next_url)

    pedido = _pedido_borrador(usuario)

    linea_existente = LineaPedido.objects.filter(pedido=pedido, producto=producto).first()
    cantidad_en_carrito = linea_existente.cantidad if linea_existente else 0
    if cantidad_en_carrito + cantidad > disponible:
        messages.error(
            request,
            f"Solo hay {disponible} unidad(es) disponible(s) de «{producto.nombre}».",
        )
        return redirect("pedidos:carrito")

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
    return redirect("pedidos:carrito")


def carrito(request):
    usuario = _usuario_actual(request)
    pedido = _pedido_borrador(usuario)
    lineas = pedido.lineas.select_related(
        "producto", "producto__categoria", "producto__inventario"
    )
    _recalcular_totales(pedido)
    whatsapp_url=_construir_url_whatsapp (lineas,pedido,usuario)
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
    linea = get_object_or_404(
        LineaPedido.objects.select_related("producto", "producto__inventario"),
        pk=linea_id,
        pedido=pedido,
    )
    nueva_cantidad = int(request.POST.get("cantidad", 1))
    if nueva_cantidad < 1:
        nueva_cantidad = 1
    disponible = stock_disponible(linea.producto)
    if nueva_cantidad > disponible:
        messages.error(
            request,
            f"Solo hay {disponible} unidad(es) disponible(s) de «{linea.producto.nombre}».",
        )
        return redirect("pedidos:carrito")
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

@require_POST
def confirmar_pedido(request):
    if not request.session.get("usuario_id"):
        messages.error(request, "Debes iniciar sesión para confirmar un pedido.", extra_tags="auth")
        return redirect("cuentas:login")

    usuario = _usuario_actual(request)

    if es_admin(usuario):
        messages.error(request, "Los administradores no pueden realizar pedidos.")
        return redirect("pedidos:carrito")
    pedido = Pedido.objects.filter(usuario=usuario, estado="borrador").first()

    if not pedido or not pedido.lineas.exists():
        messages.error(request, "Tu carrito está vacío.")
        return redirect("pedidos:carrito")

    lineas = list(
        pedido.lineas.select_related("producto", "producto__inventario")
    )
    whatsapp_url = _construir_url_whatsapp(lineas, pedido, usuario)

    try:
        with transaction.atomic():
            descontar_stock_lineas(lineas)
            pedido.estado = "confirmado"
            pedido.fecha_pedido = timezone.now()
            pedido.save(update_fields=["estado", "fecha_pedido"])
    except StockInsuficienteError as exc:
        messages.error(
            request,
            f"No hay stock suficiente de «{exc.producto.nombre}». "
            f"Disponible: {exc.disponible}, solicitado: {exc.solicitado}.",
        )
        return redirect("pedidos:carrito")

    messages.success(request, f"¡Pedido #{pedido.id_pedido} confirmado! Puedes verlo en tu historial.")

    if whatsapp_url:
        request.session["whatsapp_pendiente"] = whatsapp_url

    return redirect("pedidos:historial")


def historial_pedidos(request):
    if not request.session.get("usuario_id"):
        messages.error(request, "Debes iniciar sesión para ver tu historial de pedidos.", extra_tags="auth")
        return redirect("cuentas:login")

    usuario = _usuario_actual(request)
    pedidos = (
        Pedido.objects
        .filter(usuario=usuario)
        .exclude(estado="borrador")
        .prefetch_related("lineas__producto", "lineas__producto__categoria")
        .order_by("-fecha_pedido")
    )
    paginador = Paginator(pedidos, 4)
    pedidos_pagina = paginador.get_page(request.GET.get("page"))
    numeros_pagina = _rango_paginacion(pedidos_pagina.number, paginador.num_pages)
    whatsapp_pendiente = request.session.pop("whatsapp_pendiente", None)
    return render(request, "historial.html", {
        "pedidos": pedidos_pagina,
        "page_obj": pedidos_pagina,
        "numeros_pagina": numeros_pagina,
        "usuario": usuario,
        "whatsapp_pendiente": whatsapp_pendiente,
    })


def _rango_paginacion(actual, total):
    if total <= 7:
        return range(1, total + 1)

    paginas = {1, total, actual - 1, actual, actual + 1}
    paginas = sorted(pagina for pagina in paginas if 1 <= pagina <= total)

    rango = []
    anterior = None
    for pagina in paginas:
        if anterior and pagina - anterior > 1:
            rango.append(None)
        rango.append(pagina)
        anterior = pagina
    return rango


def _construir_url_whatsapp(lineas, pedido, usuario=None):
    numero = getattr(settings, "KUMA_WHATSAPP", "")
    if not numero or not lineas:
        return ""

    lineas_lista = list(lineas)
    items = "\n".join(
        f"  • {l.producto.nombre} x{l.cantidad} — ${l.subtotal:,}"
        for l in lineas_lista
    )

    cliente_info = ""
    if usuario and usuario.correo != "invitado@kuma.local":
        nombre_completo = f"{usuario.nombre} {usuario.apellido or ''}".strip()
        cliente_info = f"👤 *Cliente:* {nombre_completo}\n"
        if usuario.correo:
            cliente_info += f"📧 *Correo:* {usuario.correo}\n"
        if usuario.telefono:
            cliente_info += f"📞 *Teléfono:* {usuario.telefono}\n"
        cliente_info += "\n"

    mensaje = (
        "✅ *Kuma Coffee — Nuevo Pedido*\n\n"
        f"{cliente_info}"
        f"{items}\n\n"
        f"*Total: ${pedido.valor:,}*\n\n"
        "Por favor confirmar disponibilidad. ¡Gracias!"
    )
    return f"https://wa.me/{numero}?text={quote(mensaje)}"
