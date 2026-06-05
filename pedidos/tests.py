from django.test import Client, TestCase
from django.urls import reverse

from catalogo.models import InventarioProducto, Producto
from cuentas.models import Usuario
from pedidos.models import LineaPedido, Pedido


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
        inventario = InventarioProducto.objects.get(producto=self.producto)
        self.assertEqual(inventario.stock, 7)

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
