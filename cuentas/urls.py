from django.urls import path
from . import views
app_name = 'cuentas'

urlpatterns = [
    path('login', views.login,name="login"),
    path('registro', views.registro,name="registro"),
    path('restablcer', views.restablecer,name="restablecer"),

    
]