from django.urls import path

from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('detalle_producto', views.detalle_producto, name='detalle'),
]