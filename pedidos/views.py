from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q, Sum, Count
from django.db.models.functions import Coalesce
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from kuma_coffee.zona_horaria import ahora_local
from django.views.decorators.http import require_GET, require_POST

from catalogo.inventario import StockInsuficienteError, descontar_stock_lineas, stock_disponible
from catalogo.models import Producto
from cuentas.auth_utils import es_admin
from cuentas.models import Usuario

from .factura import generar_factura_pdf
from .models import LineaPedido, Pedido
from .whatsapp import construir_url_whatsapp

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
    return render(
        request,
        "carrito.html",
        {
            "pedido": pedido,
            "lineas": lineas,
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

    try:
        with transaction.atomic():
            descontar_stock_lineas(lineas)
            pedido.estado = "confirmado"
            pedido.fecha_pedido = ahora_local()
            pedido.save(update_fields=["estado", "fecha_pedido"])
    except StockInsuficienteError as exc:
        messages.error(
            request,
            f"No hay stock suficiente de «{exc.producto.nombre}». "
            f"Disponible: {exc.disponible}, solicitado: {exc.solicitado}.",
        )
        return redirect("pedidos:carrito")

    whatsapp_url = construir_url_whatsapp(lineas, pedido, usuario)

    messages.success(
        request,
        f"¡Pedido #{pedido.id_pedido} confirmado! Se abrirá WhatsApp con el detalle de tu pedido.",
    )

    if whatsapp_url:
        request.session["whatsapp_pendiente"] = whatsapp_url

    return redirect("pedidos:historial")


def historial_pedidos(request):
    if not request.session.get("usuario_id"):
        messages.error(request, "Debes iniciar sesión para ver tu historial de pedidos.", extra_tags="auth")
        return redirect("cuentas:login")

    usuario = _usuario_actual(request)
    pedidos_qs = (
        Pedido.objects.filter(usuario=usuario)
        .exclude(estado="borrador")
        .order_by("-fecha_pedido", "-id_pedido")
    )
    paginador = Paginator(pedidos_qs, 4)
    pedidos_pagina = paginador.get_page(request.GET.get("page"))

    if pedidos_pagina.object_list:
        pedidos_ids = [pedido.id_pedido for pedido in pedidos_pagina.object_list]
        pedidos_map = {
            pedido.id_pedido: pedido
            for pedido in Pedido.objects.filter(id_pedido__in=pedidos_ids).prefetch_related(
                "lineas__producto", "lineas__producto__categoria"
            )
        }
        pedidos_pagina.object_list = [
            pedidos_map[pedido_id]
            for pedido_id in pedidos_ids
            if pedido_id in pedidos_map
        ]
    numeros_pagina = _rango_paginacion(pedidos_pagina.number, paginador.num_pages)
    whatsapp_pendiente = request.session.pop("whatsapp_pendiente", None)
    return render(
        request,
        "historial.html",
        {
            "pedidos": pedidos_pagina,
            "page_obj": pedidos_pagina,
            "numeros_pagina": numeros_pagina,
            "usuario": usuario,
            "whatsapp_pendiente": whatsapp_pendiente,
        },
    )


@require_GET
def descargar_factura(request, pk):
    if not request.session.get("usuario_id"):
        messages.error(request, "Debes iniciar sesión para descargar la factura.", extra_tags="auth")
        return redirect("cuentas:login")

    usuario = _usuario_actual(request)
    pedido = get_object_or_404(
        Pedido.objects.prefetch_related("lineas__producto"),
        pk=pk,
        usuario=usuario,
    )
    if pedido.estado == "borrador":
        raise Http404

    try:
        ruta = generar_factura_pdf(pedido, usuario)
    except Exception as exc:
        raise Http404 from exc

    return FileResponse(
        ruta.open("rb"),
        as_attachment=True,
        filename=f"factura_pedido_{pedido.id_pedido}.pdf",
        content_type="application/pdf",
    )


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


def historial_admin(request):
    usuario = _usuario_actual(request)
    if not es_admin(usuario):
        messages.error(request, "Acceso restringido a administradores.")
        return redirect("inicio")

    q = request.GET.get("q", "").strip()
    estado_filtro = request.GET.get("estado", "").strip()

    pedidos_qs = (
        Pedido.objects.exclude(estado="borrador")
        .select_related("usuario")
        .order_by("-fecha_pedido", "-id_pedido")
    )

    if q:
        pedidos_qs = pedidos_qs.filter(
            Q(usuario__nombre__icontains=q)
            | Q(usuario__apellido__icontains=q)
            | Q(usuario__correo__icontains=q)
            | Q(id_pedido__icontains=q)
        )

    if estado_filtro:
        pedidos_qs = pedidos_qs.filter(estado=estado_filtro)

    resumen = Pedido.objects.exclude(estado="borrador").aggregate(
        total_pedidos=Count("id_pedido"),
        total_ventas=Coalesce(Sum("valor"), 0),
        clientes_unicos=Count("usuario", distinct=True),
    )

    paginador = Paginator(pedidos_qs, 10)
    pedidos_pagina = paginador.get_page(request.GET.get("page"))

    if pedidos_pagina.object_list:
        pedidos_ids = [p.id_pedido for p in pedidos_pagina.object_list]
        pedidos_map = {
            p.id_pedido: p
            for p in Pedido.objects.filter(id_pedido__in=pedidos_ids).prefetch_related(
                "lineas__producto", "lineas__producto__categoria"
            ).select_related("usuario")
        }
        pedidos_pagina.object_list = [
            pedidos_map[pid] for pid in pedidos_ids if pid in pedidos_map
        ]

    numeros_pagina = _rango_paginacion(pedidos_pagina.number, paginador.num_pages)

    return render(
        request,
        "historial_admin.html",
        {
            "pedidos": pedidos_pagina,
            "page_obj": pedidos_pagina,
            "numeros_pagina": numeros_pagina,
            "resumen": resumen,
            "q": q,
            "estado_filtro": estado_filtro,
        },
    )


@require_GET
def factura_admin(request, pk):
    usuario = _usuario_actual(request)
    if not es_admin(usuario):
        messages.error(request, "Acceso restringido a administradores.")
        return redirect("inicio")

    pedido = get_object_or_404(
        Pedido.objects.prefetch_related("lineas__producto").select_related("usuario"),
        pk=pk,
    )
    if pedido.estado == "borrador":
        raise Http404

    try:
        ruta = generar_factura_pdf(pedido, pedido.usuario)
    except Exception as exc:
        raise Http404 from exc

    return FileResponse(
        ruta.open("rb"),
        as_attachment=True,
        filename=f"factura_pedido_{pedido.id_pedido}.pdf",
        content_type="application/pdf",
    )
