from django.db import models

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=32)
    apellido = models.CharField(max_length=32, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(max_length=32)
    password = models.CharField(max_length=255, db_column="contraseña")
    rol = models.CharField(max_length=20, default="cliente")

    class Meta:
        db_table = "usuario"
        ordering = ["id_usuario"]

    def __str__(self):
        return f"{self.nombre} ({self.correo})"
