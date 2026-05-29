from django.shortcuts import render
from django.db.models import Q
from catalogo.models import Producto


def sobre_nosotros(request):
    return render(request, "sobre_nosotros.html")


def manual_usuario(request):
    return render(request, "manual_usuario.html")


def inicio(request):
    # Todos los productos disponibles (sin límite), mostrados de 3 en 3 en el slider
    qs = (
        Producto.objects
        .select_related("categoria", "inventario")
        .filter(
            Q(inventario__stock__gt=0) |
            (Q(inventario__isnull=True) & Q(stock__gt=0))
        )
        .order_by("nombre")
    )
    # Si no hay ninguno disponible, mostrar todos los productos igualmente
    if not qs.exists():
        qs = (
            Producto.objects
            .select_related("categoria",'inventario')
            .order_by("nombre")
        )
    return render(request, "inicio.html", {"productos_destacados": qs})
