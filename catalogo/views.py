import os
import uuid
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProductoForm
from pathlib import Path

from .models import Producto,Categoria

def lista(request):
    categorias = Categoria.objects.prefetch_related(
        "productos",
        "productos__altura",
        "productos__tostion",
    ).all()
    productos_sin_categoria = (
        Producto.objects.filter(categoria__isnull=True)
        .select_related("altura", "tostion")
    )
    return render(
        request,
        "catalogo.html",
        {
            "categorias": categorias,
            "productos_sin_categoria": productos_sin_categoria,
        },
    )


def detalle_producto(request, pk):
    producto = get_object_or_404(
        Producto.objects.select_related("categoria", "altura", "tostion"),
        pk=pk,
    )
    return render(request, "detalle_producto.html", {"producto": producto})



def lista_productos(request):
    # if not _es_admin(request):
    #     return redirect("cuentas:login")
    productos = Producto.objects.select_related(
        "categoria", "altura", "tostion"
    ).order_by("nombre")
    return render(request, "lista_productos.html", {
        "productos": productos,
        
    })


def crear_producto(request):
    # if not _es_admin(request):
    #     return redirect("cuentas:login")
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            archivo = request.FILES.get("imagen_file")
            if archivo:
                producto.imagen = _guardar_imagen(archivo)
            producto.save()
            messages.success(request, f'Producto "{producto.nombre}" creado correctamente.')
            return redirect("catalogo:lista_productos")
    else:
        form = ProductoForm()
    return render(request, "admin_producto_form.html", {"form": form, "accion": "Agregar"})


def editar_producto(request, pk):
    # if not _es_admin(request):
    #     return redirect("cuentas:login")
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            prod = form.save(commit=False)
            archivo = request.FILES.get("imagen_file")
            if archivo:
                prod.imagen = _guardar_imagen(archivo)
            prod.save()
            messages.success(request, f'Producto "{prod.nombre}" actualizado correctamente.')
            return redirect("catalogo:lista_productos")
    else:
        form = ProductoForm(instance=producto)
    return render(request, "admin_producto_form.html", {"form": form, "accion": "Editar", "producto": producto})


def eliminar_producto(request, pk):
    # if not _es_admin(request):
    #     return redirect("cuentas:login")
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        nombre = producto.nombre
        producto.delete()
        messages.success(request, f'Producto "{nombre}" eliminado.')
        return redirect("catalogo:lista_productos")
    return render(request, "confirmar_eliminar.html", {"producto": producto})

def _guardar_imagen(archivo):
    """Guarda el archivo subido en media/productos/ y retorna la ruta relativa."""
    carpeta = Path(settings.MEDIA_ROOT) / "productos"
    carpeta.mkdir(parents=True, exist_ok=True)
    ext = os.path.splitext(archivo.name)[1].lower()
    nombre_unico = f"{uuid.uuid4().hex}{ext}"
    ruta_completa = carpeta / nombre_unico
    with open(ruta_completa, "wb") as f:
        for chunk in archivo.chunks():
            f.write(chunk)
    return f"productos/{nombre_unico}"