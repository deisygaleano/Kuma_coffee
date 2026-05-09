from django.urls import path
from . import views
app_name = 'cuentas'

urlpatterns = [
    path('login', views.login,name="login"),
    path('registro', views.registro,name="registro"),
    path('logout', views.logout,name="logout"),
    path('restablecer', views.restablecer,name="restablecer"),
    path('restablcer', views.restablecer,name="restablecer_legacy"),

    
]
