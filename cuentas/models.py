from django.db import models

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=32)
    apellido = models.CharField(max_length=32, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(max_length=254)
    password = models.CharField(max_length=255, db_column="contraseña",blank=True, null=True)
    rol = models.CharField(max_length=20, default="cliente")
    google_id= models.CharField(max_length=128, blank=True, null=True,unique=True)
    foto = models.FileField(upload_to="usuarios/", blank=True, null=True)


    class Meta:
        db_table = "usuario"
        ordering = ["id_usuario"]

    def __str__(self):
        return f"{self.nombre} ({self.correo})"
