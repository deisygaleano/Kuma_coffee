from pathlib import Path

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def formato_peso(valor):
    try:
        entero = int(round(float(valor)))
        return f"${entero:,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(valor)


def ruta_factura_pedido(pedido_id):
    facturas_dir = Path(settings.MEDIA_ROOT) / "facturas"
    facturas_dir.mkdir(parents=True, exist_ok=True)
    return facturas_dir / f"pedido_{pedido_id}.pdf"


def ruta_logo_proyecto():
    return Path(settings.MEDIA_ROOT).parent / "inicio" / "static" / "imagenes" / "logoproyecto.png"


def _encabezado_factura(titulo, subtitulo):
    ruta_logo = ruta_logo_proyecto()
    if not ruta_logo.is_file():
        return [
            Paragraph("Kuma Coffee", titulo),
            Paragraph("Factura de pedido", subtitulo),
            Spacer(1, 0.4 * cm),
        ]

    logo_ancho = 3.5 * cm
    logo_alto = logo_ancho * (408 / 612)
    logo = Image(str(ruta_logo), width=logo_ancho, height=logo_alto)
    logo.hAlign = "LEFT"

    tabla_texto = Table(
        [
            [Paragraph("Kuma Coffee", titulo)],
            [Paragraph("Factura de pedido", subtitulo)],
        ],
        colWidths=[12.2 * cm],
    )
    tabla_texto.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    encabezado = Table([[logo, tabla_texto]], colWidths=[4 * cm, 12.2 * cm])
    encabezado.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return [encabezado, Spacer(1, 0.4 * cm)]


def generar_factura_pdf(pedido, usuario):
    lineas = list(
        pedido.lineas.select_related("producto", "producto__categoria").order_by(
            "producto__nombre"
        )
    )
    ruta = ruta_factura_pedido(pedido.id_pedido)

    styles = getSampleStyleSheet()
    titulo = ParagraphStyle(
        "TituloFactura",
        parent=styles["Heading1"],
        fontSize=20,
        spaceAfter=8,
        textColor=colors.HexColor("#7a6522"),
    )
    subtitulo = ParagraphStyle(
        "SubtituloFactura",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#4a4034"),
        spaceAfter=4,
    )

    doc = SimpleDocTemplate(
        str(ruta),
        pagesize=letter,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    elementos = _encabezado_factura(titulo, subtitulo)

    fecha = pedido.fecha_pedido or timezone.now()
    nombre_cliente = f"{usuario.nombre} {usuario.apellido or ''}".strip()
    info = [
        ["Pedido", f"#{pedido.id_pedido}"],
        ["Fecha", fecha.strftime("%d/%m/%Y %H:%M")],
        ["Cliente", nombre_cliente],
        ["Correo", usuario.correo or "—"],
        ["Teléfono", usuario.telefono or "—"],
        ["Estado", pedido.estado.title()],
    ]
    tabla_info = Table(info, colWidths=[3.2 * cm, 12 * cm])
    tabla_info.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#3d3428")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elementos.extend([tabla_info, Spacer(1, 0.6 * cm)])

    filas = [["Producto", "Cant.", "Precio unit.", "Subtotal"]]
    for linea in lineas:
        filas.append(
            [
                linea.producto.nombre,
                str(linea.cantidad),
                formato_peso(linea.precio_unitario),
                formato_peso(linea.subtotal),
            ]
        )
    filas.append(["", "", "Total", formato_peso(pedido.valor)])

    tabla_productos = Table(
        filas,
        colWidths=[8.5 * cm, 1.8 * cm, 3 * cm, 3 * cm],
        repeatRows=1,
    )
    tabla_productos.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e0d4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#3d3428")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#c9b896")),
                ("LINEABOVE", (2, -1), (-1, -1), 1, colors.HexColor("#7a6522")),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (2, -1), (-1, -1), colors.HexColor("#f5f0e8")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elementos.extend(
        [
            tabla_productos,
            Spacer(1, 0.8 * cm),
            Paragraph(
                "Gracias por tu compra. Kuma Coffee — café de especialidad.",
                subtitulo,
            ),
        ]
    )

    doc.build(elementos)
    return ruta
