from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('lista_productos/', views.lista_productos, name='lista_productos'),
    path('detalle/<int:pk>/', views.detalle_producto, name='detalle'),
    path('admin/inventario/', views.inventario_productos, name='inventario_productos'),
    path('admin/productos/', views.lista_productos, name='lista_productos'),
    path('admin/productos/crear/', views.crear_producto, name='crear_producto'),
    path('admin/productos/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('admin/productos/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    
    
]
