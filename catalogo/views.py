import os
import uuid
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProductoForm
from pathlib import Path

from cuentas.auth_utils import usuario_es_admin
from .models import InventarioProducto, Producto, Categoria

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
    if not _es_admin(request):
        return redirect("cuentas:login")
    productos = Producto.objects.select_related(
        "categoria", "altura", "tostion", "inventario"
    ).order_by("nombre")
    return render(request, "lista_productos.html", {
        "productos": productos,
        
    })


def inventario_productos(request):
    if not _es_admin(request):
        return redirect("cuentas:login")
    if request.method == "POST":
        producto = get_object_or_404(Producto, pk=request.POST.get("producto_id"))
        try:
            stock = int(request.POST.get("stock", 0))
            stock_minimo = int(request.POST.get("stock_minimo", 0))
        except (TypeError, ValueError):
            messages.error(request, "Ingresa valores numericos validos para el inventario.")
            return redirect("catalogo:inventario_productos")

        if stock < 0 or stock_minimo < 0:
            messages.error(request, "El stock no puede ser negativo.")
            return redirect("catalogo:inventario_productos")

        InventarioProducto.objects.update_or_create(
            producto=producto,
            defaults={"stock": stock, "stock_minimo": stock_minimo},
        )
        messages.success(request, f'Inventario de "{producto.nombre}" actualizado.')
        return redirect("catalogo:inventario_productos")

    _asegurar_inventario_productos()
    productos = Producto.objects.select_related("categoria", "inventario").order_by("nombre")
    busqueda = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()

    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda)
            | Q(categoria__nombre__icontains=busqueda)
            | Q(slug__icontains=busqueda)
        )

    productos = list(productos)
    if estado:
        productos = [p for p in productos if p.estado_inventario == estado]

    resumen = {
        "total_productos": len(productos),
        "unidades": sum(p.stock_actual for p in productos),
        "agotados": sum(1 for p in productos if p.estado_inventario == "agotado"),
        "stock_bajo": sum(1 for p in productos if p.estado_inventario == "bajo"),
    }

    return render(
        request,
        "inventario_productos.html",
        {
            "productos": productos,
            "busqueda": busqueda,
            "estado": estado,
            "resumen": resumen,
        },
    )


def crear_producto(request):
    if not _es_admin(request):
        return redirect("cuentas:login")
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            archivo = request.FILES.get("imagen_file")
            if archivo:
                producto.imagen = _guardar_imagen(archivo)
            producto.save()
            _guardar_inventario_desde_form(producto, form)
            messages.success(request, f'Producto "{producto.nombre}" creado correctamente.')
            return redirect("catalogo:lista_productos")
    else:
        form = ProductoForm()
    return render(request, "admin_producto_form.html", {"form": form, "accion": "Agregar"})


def editar_producto(request, pk):
    if not _es_admin(request):
        return redirect("cuentas:login")
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            prod = form.save(commit=False)
            archivo = request.FILES.get("imagen_file")
            if archivo:
                prod.imagen = _guardar_imagen(archivo)
            prod.save()
            _guardar_inventario_desde_form(prod, form)
            messages.success(request, f'Producto "{prod.nombre}" actualizado correctamente.')
            return redirect("catalogo:lista_productos")
    else:
        form = ProductoForm(instance=producto)
    return render(request, "admin_producto_form.html", {"form": form, "accion": "Editar", "producto": producto})


def eliminar_producto(request, pk):
    if not _es_admin(request):
        return redirect("cuentas:login")
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


def _guardar_inventario_desde_form(producto, form):
    InventarioProducto.objects.update_or_create(
        producto=producto,
        defaults={
            "stock": form.cleaned_data["stock"],
            "stock_minimo": form.cleaned_data["stock_minimo"],
        },
    )


def _asegurar_inventario_productos():
    productos_sin_inventario = Producto.objects.filter(inventario__isnull=True)
    inventarios = [
        InventarioProducto(
            producto=producto,
            stock=producto.stock,
            stock_minimo=producto.stock_minimo,
        )
        for producto in productos_sin_inventario
    ]
    InventarioProducto.objects.bulk_create(inventarios, ignore_conflicts=True)


def _es_admin(request):
    if usuario_es_admin(request):
        return True
    messages.error(request, "Debes iniciar sesion como administrador para acceder a esta seccion.")
    return False
