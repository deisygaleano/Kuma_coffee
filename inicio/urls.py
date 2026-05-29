from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('' , views.inicio,name="inicio"),
    path('sobre-nosotros/', views.sobre_nosotros,name="sobre_nosotros"),
    path('manual-usuario/', views.manual_usuario,name="manual_usuario"),
]
