from types import SimpleNamespace

from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from catalogo.models import InventarioProducto, Producto
from cuentas.models import Usuario
from pedidos.models import LineaPedido, Pedido
from pedidos.whatsapp import construir_mensaje_pedido, construir_url_whatsapp


class MensajeWhatsAppTests(SimpleTestCase):
    def test_mensaje_pedido_incluye_secciones_principales(self):
        usuario = SimpleNamespace(
            nombre="Ana",
            apellido="López",
            correo="ana@test.com",
            telefono="3001234567",
        )
        producto = SimpleNamespace(
            nombre="Café Especial",
            descripcion="Grano de origen único con notas cítricas.",
        )
        linea = SimpleNamespace(
            producto=producto,
            cantidad=2,
            precio_unitario=15000,
            subtotal=30000,
        )
        pedido = SimpleNamespace(
            id_pedido=42,
            valor=30000,
            fecha_pedido=timezone.now(),
        )

        mensaje = construir_mensaje_pedido([linea], pedido, usuario)

        self.assertIn("Hola, Kuma Coffee", mensaje)
        self.assertIn("Numero: #42", mensaje)
        self.assertIn("MI PEDIDO", mensaje)
        self.assertIn("CLIENTE", mensaje)
        self.assertIn("PRODUCTOS", mensaje)
        self.assertIn("Café Especial", mensaje)
        self.assertIn("notas cítricas", mensaje)
        self.assertIn("$30.000", mensaje)
        self.assertIn("TOTAL ESTIMADO:", mensaje)
        self.assertIn("Quedo atento", mensaje)
        self.assertNotIn("confirmara disponibilidad", mensaje)

    def test_url_whatsapp_usa_formato_wa_me(self):
        producto = SimpleNamespace(nombre="Café")
        linea = SimpleNamespace(
            producto=producto,
            cantidad=1,
            precio_unitario=10000,
            subtotal=10000,
        )
        pedido = SimpleNamespace(
            id_pedido=1,
            valor=10000,
            fecha_pedido=timezone.now(),
        )

        with self.settings(KUMA_WHATSAPP="573001234567"):
            url = construir_url_whatsapp([linea], pedido, None)

        self.assertTrue(url.startswith("https://wa.me/573001234567?text="))


class StockPedidoTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create(
            nombre="Cliente",
            apellido="Test",
            correo="cliente@test.com",
            password="hash",
            rol="cliente",
        )
        self.producto = Producto.objects.create(
            nombre="Cafe Test",
            precio=10000,
            stock=10,
            stock_minimo=2,
        )
        InventarioProducto.objects.create(
            producto=self.producto,
            stock=10,
            stock_minimo=2,
        )
        session = self.client.session
        session["usuario_id"] = self.usuario.id_usuario
        session.save()

    def _pedido_borrador(self):
        return Pedido.objects.create(
            usuario=self.usuario,
            estado="borrador",
            cantidad=0,
            valor=0,
        )

    def test_confirmar_pedido_descuenta_stock(self):
        pedido = self._pedido_borrador()
        LineaPedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=3,
            precio_unitario=10000,
        )

        response = self.client.post(reverse("pedidos:confirmar"))

        self.assertEqual(response.status_code, 302)
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, "confirmado")
        self.assertEqual(pedido.lineas.count(), 1)
        inventario = InventarioProducto.objects.get(producto=self.producto)
        self.assertEqual(inventario.stock, 7)

    def test_historial_muestra_productos_tras_confirmar(self):
        pedido = self._pedido_borrador()
        LineaPedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=2,
            precio_unitario=10000,
        )

        self.client.post(reverse("pedidos:confirmar"))
        response = self.client.get(reverse("pedidos:historial"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cafe Test")
    def test_descargar_factura_genera_pdf_al_hacer_clic(self):
        pedido = self._pedido_borrador()
        LineaPedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=2,
            precio_unitario=10000,
        )

        self.client.post(reverse("pedidos:confirmar"))
        pedido.refresh_from_db()

        response = self.client.get(reverse("pedidos:factura", args=[pedido.id_pedido]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response.get("Content-Disposition", ""))

    def test_confirmar_pedido_sin_stock_suficiente_no_confirma(self):
        pedido = self._pedido_borrador()
        LineaPedido.objects.create(
            pedido=pedido,
            producto=self.producto,
            cantidad=15,
            precio_unitario=10000,
        )

        response = self.client.post(reverse("pedidos:confirmar"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("pedidos:carrito"))
        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, "borrador")
        inventario = InventarioProducto.objects.get(producto=self.producto)
        self.assertEqual(inventario.stock, 10)

    def test_agregar_al_carrito_rechaza_producto_agotado(self):
        inventario = InventarioProducto.objects.get(producto=self.producto)
        inventario.stock = 0
        inventario.save(update_fields=["stock"])

        response = self.client.post(
            reverse("pedidos:agregar"),
            {"producto_id": self.producto.id_producto, "cantidad": 1},
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            LineaPedido.objects.filter(
                pedido__usuario=self.usuario,
                pedido__estado="borrador",
                producto=self.producto,
            ).exists()
        )

    def test_agregar_al_carrito_rechaza_cantidad_mayor_al_stock(self):
        response = self.client.post(
            reverse("pedidos:agregar"),
            {"producto_id": self.producto.id_producto, "cantidad": 12},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("pedidos:carrito"))
        self.assertFalse(
            LineaPedido.objects.filter(
                pedido__usuario=self.usuario,
                pedido__estado="borrador",
            ).exists()
        )
