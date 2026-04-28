from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('lista_productos/', views.lista_productos, name='lista_productos'),
    path('detalle/<int:pk>/', views.detalle_producto, name='detalle'),
    
    
]
