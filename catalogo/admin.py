from django.contrib import admin

from .models import Altura, Categoria, InventarioProducto, Producto, Tostion


admin.site.register(Categoria)
admin.site.register(Altura)
admin.site.register(Tostion)
admin.site.register(Producto)
admin.site.register(InventarioProducto)
