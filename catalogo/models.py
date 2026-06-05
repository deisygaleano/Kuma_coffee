import re

from django.db import models

_UNIDAD_ALTURA_RE = re.compile(
    r"(?i)\b(m\.?\s*s\.?\s*n\.?\s*m\.?|msnm|msnv|metros\s+sobre\s+(el\s+)?nivel\s+del\s+mar)\b"
)
class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=40, unique=True)

    class Meta:
        db_table = "categoria"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre
class Altura(models.Model):
    id_altura = models.AutoField(primary_key=True)
    metros = models.CharField(max_length=12, blank=True, null=True)
    descripcion = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = "altura"
        ordering = ["metros"]

    def __str__(self):
        return self.metros_formateado

    @property
    def metros_formateado(self):
        if not self.metros:
            return ""
        return _UNIDAD_ALTURA_RE.sub("M.S.N.M", self.metros.strip())


class Tostion(models.Model):
    id_tostion = models.AutoField(primary_key=True)
    tipo = models.CharField(max_length=20)
    descripcion = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "tostion"
        ordering = ["tipo"]

    def __str__(self):
        return self.tipo


class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=32)
    altura = models.ForeignKey(
        Altura,
        models.SET_NULL,
        db_column="id_altura",
        blank=True,
        null=True,
        related_name="productos",
    )
    tostion = models.ForeignKey(
        Tostion,
        models.SET_NULL,
        db_column="id_tostion",
        blank=True,
        null=True,
        related_name="productos",
    )
    descripcion = models.TextField(blank=True, null=True)
    precio = models.IntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    imagen = models.CharField(max_length=255, blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria,
        models.SET_NULL,
        db_column="id_categoria",
        blank=True,
        null=True,
        related_name="productos",
    )

    class Meta:
        db_table = "producto"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def stock_actual(self):
        inventario = getattr(self, "inventario", None)
        return inventario.stock if inventario else self.stock

    @property
    def stock_minimo_actual(self):
        inventario = getattr(self, "inventario", None)
        return inventario.stock_minimo if inventario else self.stock_minimo

    @property
    def estado_inventario(self):
        stock = self.stock_actual
        stock_minimo = self.stock_minimo_actual
        if stock == 0:
            return "agotado"
        if stock <= stock_minimo:
            return "bajo"
        return "disponible"


class InventarioProducto(models.Model):
    id_inventario = models.AutoField(primary_key=True)
    producto = models.OneToOneField(
        Producto,
        models.CASCADE,
        db_column="id_producto",
        related_name="inventario",
    )
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=5)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "inventario_producto"
        ordering = ["producto__nombre"]

    def __str__(self):
        return f"Inventario - {self.producto.nombre}"

