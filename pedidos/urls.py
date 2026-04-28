from django.urls import path
from . import views
app_name = 'pedidos'

urlpatterns = [
    path('', views.carrito,name="carrito"),
    path('agregar/', views.agregar_al_carrito, name="agregar"),

    
]
