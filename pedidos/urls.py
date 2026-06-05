from django.urls import path
from . import views
app_name = 'pedidos'

urlpatterns = [
    path('', views.carrito, name="carrito"),
    path('agregar/', views.agregar_al_carrito, name="agregar"),
    path('actualizar/<int:linea_id>/', views.actualizar_cantidad, name="actualizar"),
    path('eliminar/<int:linea_id>/', views.eliminar_linea, name="eliminar"),
    path('confirmar/', views.confirmar_pedido, name="confirmar"),
    path('historial/', views.historial_pedidos, name="historial"),
    path('factura/<int:pk>/', views.descargar_factura, name="factura"),
]
