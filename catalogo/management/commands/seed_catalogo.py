from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from catalogo.models import Altura, Categoria, InventarioProducto, Producto, Tostion

CATEGORIAS = [
    {"id_categoria": 1, "nombre": "Grano entero", "slug": "grano-entero"},
    {"id_categoria": 2, "nombre": "Molido", "slug": "molido"},
    {"id_categoria": 3, "nombre": "Edicion especial", "slug": "edicion-especial"},
]

ALTURAS = [
    {"id_altura": 1, "metros": "1800 msnm", "descripcion": "clima fresco ideal para cafe"},
    {"id_altura": 2, "metros": "2000 msnm", "descripcion": "altura premium"},
    {"id_altura": 3, "metros": "1500 msnm", "descripcion": "Clima templado"},
    {"id_altura": 4, "metros": "2200 msnm", "descripcion": "Cafe de alta montaña"},
]

TOSTIONES = [
    {"id_tostion": 1, "tipo": "Suave", "descripcion": "Ligero y delicado"},
    {"id_tostion": 2, "tipo": "Media", "descripcion": "Equilibrado y aromatico"},
    {"id_tostion": 3, "tipo": "Oscura", "descripcion": "Intenso y fuerte"},
]

PRODUCTOS = [
    {
        "id_producto": 1,
        "nombre": "Geisha",
        "descripcion": "Suave",
        "id_altura": 1,
        "id_tostion": 1,
        "precio": 25000,
        "imagen": "productos/4de10f0e2e35487881a240329c8221ba.png",
        "id_categoria": 1,
        "stock": 0,
        "stock_minimo": 5,
    },
    {
        "id_producto": 2,
        "nombre": "Variedad 2000",
        "descripcion": "Fuerte",
        "id_altura": 2,
        "id_tostion": 2,
        "precio": 30000,
        "imagen": "productos/b1d506091fa24389bb9f99670aeb17e2.png",
        "id_categoria": 3,
        "stock": 0,
        "stock_minimo": 5,
    },
    {
        "id_producto": 4,
        "nombre": "variedad 2000",
        "descripcion": "fuerte",
        "id_altura": 2,
        "id_tostion": 2,
        "precio": 30000,
        "imagen": "productos/b9ce13817df748709726eb8d024e1187.png",
        "id_categoria": 3,
        "stock": 0,
        "stock_minimo": 5,
    },
    {
        "id_producto": 7,
        "nombre": "castillo",
        "descripcion": "Suave",
        "id_altura": 1,
        "id_tostion": 3,
        "precio": 40000,
        "imagen": "productos/bcbc8c763b1946dd8b512ae1fc1071a0.png",
        "id_categoria": 1,
        "stock": 0,
        "stock_minimo": 5,
    },
]

INVENTARIOS = [
    {"id_producto": 7, "stock": 1, "stock_minimo": 5},
    {"id_producto": 1, "stock": 1, "stock_minimo": 5},
    {"id_producto": 2, "stock": 0, "stock_minimo": 5},
    {"id_producto": 4, "stock": 0, "stock_minimo": 5},
]

ADMIN_USER = {
    "username": "listo",
    "email": "listo@gmail.com",
    "password_hash": "pbkdf2_sha256$1200000$uW1XoSjT9t9zu3h2TNDZMr$lJrFtrfl0onAY7n3F3Sr8KAaR5PVAOrBvL8Cl3+yS3s=",
}


class Command(BaseCommand):
    help = "Carga el catálogo (categorías, alturas, tostiones, productos, inventario) y el admin original en una base de datos nueva."

    def handle(self, *args, **options):
        for data in CATEGORIAS:
            pk = data.pop("id_categoria")
            Categoria.objects.update_or_create(id_categoria=pk, defaults=data)
        self.stdout.write(self.style.SUCCESS(f"Categorías: {len(CATEGORIAS)}"))

        for data in ALTURAS:
            pk = data.pop("id_altura")
            Altura.objects.update_or_create(id_altura=pk, defaults=data)
        self.stdout.write(self.style.SUCCESS(f"Alturas: {len(ALTURAS)}"))

        for data in TOSTIONES:
            pk = data.pop("id_tostion")
            Tostion.objects.update_or_create(id_tostion=pk, defaults=data)
        self.stdout.write(self.style.SUCCESS(f"Tostiones: {len(TOSTIONES)}"))

        for data in PRODUCTOS:
            pk = data.pop("id_producto")
            altura_id = data.pop("id_altura")
            tostion_id = data.pop("id_tostion")
            categoria_id = data.pop("id_categoria")
            Producto.objects.update_or_create(
                id_producto=pk,
                defaults={
                    **data,
                    "altura_id": altura_id,
                    "tostion_id": tostion_id,
                    "categoria_id": categoria_id,
                },
            )
        self.stdout.write(self.style.SUCCESS(f"Productos: {len(PRODUCTOS)}"))

        for data in INVENTARIOS:
            producto_id = data.pop("id_producto")
            InventarioProducto.objects.update_or_create(
                producto_id=producto_id, defaults=data
            )
        self.stdout.write(self.style.SUCCESS(f"Inventarios: {len(INVENTARIOS)}"))

        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=ADMIN_USER["username"],
            defaults={
                "email": ADMIN_USER["email"],
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        user.password = ADMIN_USER["password_hash"]
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        accion = "creado" if created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuario admin '{ADMIN_USER['username']}' {accion} (usa la misma contraseña de tu entorno local)."
            )
        )
