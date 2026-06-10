from django.urls import path
from . import views
app_name = 'cuentas'

urlpatterns = [
   path('login', views.login, name="login"),
    path('registro', views.registro, name="registro"),
    path('logout', views.logout, name="logout"),
    path('restablecer', views.restablecer, name="restablecer"),
    path('restablcer', views.restablecer, name="restablecer_legacy"),
    path('cambiar-password', views.cambiar_password, name="cambiar_password"),
    path('actualizar-foto', views.actualizar_foto, name="actualizar_foto"),
    path('google/login', views.google_login, name="google_login"),
    path('google/callback', views.google_callback, name="google_callback"),
    path('tutorial-visto', views.marcar_tutorial_visto, name="tutorial_visto"),
]
