from urllib.parse import quote

from django.conf import settings
from kuma_coffee.zona_horaria import ahora_local

from .factura import formato_peso


def _fecha_pedido(pedido):
    fecha = pedido.fecha_pedido or ahora_local()
    return fecha.strftime("%d/%m/%Y"), fecha.strftime("%H:%M")


def _texto_descripcion(texto, maximo=120):
    descripcion = (texto or "").strip()
    if not descripcion:
        return ""
    if len(descripcion) > maximo:
        return f"{descripcion[:maximo].rstrip()}..."
    return descripcion


def _bloque_cliente(usuario):
    if not usuario or usuario.correo == "invitado@kuma.local":
        return ""

    nombre = f"{usuario.nombre} {usuario.apellido or ''}".strip()
    lineas = [
        "",
        "*CLIENTE*",
        f"Nombre: {nombre}",
    ]
    if usuario.correo:
        lineas.append(f"Correo: {usuario.correo}")
    if usuario.telefono:
        lineas.append(f"Telefono: {usuario.telefono}")
    return "\n".join(lineas)


def _bloque_productos(lineas_pedido):
    if not lineas_pedido:
        return ""

    detalle = ["", "*PRODUCTOS*"]
    for indice, linea in enumerate(lineas_pedido, start=1):
        nombre = linea.producto.nombre
        cantidad = linea.cantidad
        unitario = formato_peso(linea.precio_unitario)
        subtotal = formato_peso(linea.subtotal)
        descripcion = _texto_descripcion(getattr(linea.producto, "descripcion", ""))
        detalle.append(f"{indice}) {nombre}")
        if descripcion:
            detalle.append(f"   {descripcion}")
        detalle.append(f"   {cantidad} x {unitario} = *{subtotal}*")
    return "\n".join(detalle)


def construir_mensaje_pedido(lineas, pedido, usuario=None):
    lineas_lista = list(lineas)
    if not lineas_lista:
        return ""

    fecha, hora = _fecha_pedido(pedido)
    total = formato_peso(pedido.valor)
    unidades = sum(linea.cantidad for linea in lineas_lista)

    partes = [
        "Hola, Kuma Coffee.",
        "",
        "Les escribo para enviar el detalle de mi pedido",
        "registrado en la pagina web:",
        "",
        "*MI PEDIDO*",
        f"Numero: #{pedido.id_pedido}",
        f"Fecha: {fecha}",
        f"Hora: {hora}",
        f"Items: {len(lineas_lista)} | Unidades: {unidades}",
    ]

    cliente = _bloque_cliente(usuario)
    if cliente:
        partes.append(cliente)

    productos = _bloque_productos(lineas_lista)
    if productos:
        partes.append(productos)

    partes.extend(
        [
            "",
            f"*TOTAL ESTIMADO: {total}*",
            "",
            "Quedo atento a su respuesta para coordinar",
            "el pedido. Muchas gracias.",
        ]
    )

    return "\n".join(partes)


def construir_url_whatsapp(lineas, pedido, usuario=None):
    numero = getattr(settings, "KUMA_WHATSAPP", "")
    mensaje = construir_mensaje_pedido(lineas, pedido, usuario)
    if not numero or not mensaje:
        return ""
    return f"https://wa.me/{numero}?text={quote(mensaje)}"
