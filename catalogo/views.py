from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .models import Producto,Categoria

def lista(request):
    categorias = Categoria.objects.prefetch_related("productos").all()
    productos_sin_categoria = Producto.objects.filter(categoria__isnull=True)
    return render(
        request,
        "catalogo.html",
        {
            "categorias": categorias,
            "productos_sin_categoria": productos_sin_categoria,
        },
    )


def detalle_producto(request, pk):
    producto = get_object_or_404(Producto.objects.select_related("categoria"), pk=pk)
    return render(request, "detalle_producto.html", {"producto": producto})

def lista_productos(request):
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "crear":
            nombre = request.POST.get("nombre", "").strip()
            precio = request.POST.get("precio", "").strip()
            categoria = request.POST.get("categoria", "").strip()
            imagen = request.FILES.get("imagen")

            if not nombre or not precio or not categoria or not imagen:
                messages.error(request, "Completa nombre, precio, categoria e imagen para guardar el producto.")
            else:
                Producto.objects.create(
                    nombre=nombre,
                    precio=precio,
                    categoria=categoria,
                    imagen=imagen,
                )
                messages.success(request, "Producto agregado correctamente.")

            return redirect("catalogo:lista_productos")

        if accion == "actualizar_imagen":
            producto = get_object_or_404(Producto, pk=request.POST.get("producto_id"))
            nueva_imagen = request.FILES.get("nueva_imagen")

            if nueva_imagen:
                producto.imagen = nueva_imagen
                producto.save(update_fields=["imagen"])
                messages.success(request, f"Imagen actualizada para {producto.nombre}.")
            else:
                messages.error(request, "Selecciona una imagen antes de actualizar.")

            return redirect("catalogo:lista_productos")

        if accion == "eliminar":
            producto = get_object_or_404(Producto, pk=request.POST.get("producto_id"))
            nombre = producto.nombre
            producto.delete()
            messages.success(request, f"{nombre} fue eliminado del catalogo.")
            return redirect("catalogo:lista_productos")

    productos = Producto.objects.order_by("nombre")
    return render(request, "lista_productos.html", {"productos": productos})
