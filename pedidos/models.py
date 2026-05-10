from django.db import models
from catalogo.models import Producto
from cuentas.models import Usuario


class Pedido(models.Model):
    id_pedido = models.AutoField(primary_key=True)
    cantidad = models.IntegerField(default=0)
    valor = models.IntegerField(default=0)
    estado = models.CharField(max_length=20, default="borrador")
    fecha_pedido= models.DateTimeField(null=True, blank=True)
    usuario = models.ForeignKey(
        Usuario,
        models.CASCADE,
        db_column="id_usuario",
        related_name="pedidos",
    )

    class Meta:
        db_table = "pedido"
        ordering = ["-id_pedido"]

    def __str__(self):
        return f"Pedido #{self.id_pedido} - {self.estado}"


class LineaPedido(models.Model):
    id_linea = models.AutoField(primary_key=True)
    producto = models.ForeignKey(
        Producto,
        models.CASCADE,
        db_column="id_producto",
        related_name="lineas_pedido",
    )
    pedido = models.ForeignKey(
        Pedido,
        models.CASCADE,
        db_column="id_pedido",
        related_name="lineas",
    )
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "producto_pedido"
        constraints = [
            models.UniqueConstraint(
                fields=["producto", "pedido"],
                name="uq_producto_pedido",
            )
        ]

    @property
    def subtotal(self):
        return (self.precio_unitario or 0) * self.cantidad
