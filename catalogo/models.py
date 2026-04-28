from django.db import models
class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=32, unique=True)
    slug = models.SlugField(max_length=40, unique=True)

    class Meta:
        db_table = "categoria"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=32)
    altura = models.CharField(max_length=10, blank=True, null=True,db_column='id_altura')
    tostion = models.CharField(max_length=10, blank=True, null=True,db_column='id_tostion')
    descripcion = models.CharField(max_length=50, blank=True, null=True)
    precio = models.IntegerField(default=0)
    imagen = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True, null=True)
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

