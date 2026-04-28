from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Q
from django.shortcuts import redirect, render

from .models import Usuario


def login(request):
    if request.method == "POST":
        correo = request.POST.get("correo", "").strip().lower()
        password = request.POST.get("password", "")
        usuario = Usuario.objects.filter(correo=correo).first()

        if usuario and check_password(password, usuario.password):
            request.session["usuario_id"] = usuario.id_usuario
            messages.success(request, "Inicio de sesión exitoso.")
            return redirect("catalogo:lista")

        messages.error(request, "Credenciales inválidas.")

    return render(request, "login.html")


def registro(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        apellido = request.POST.get("apellido", "").strip()
        correo = request.POST.get("correo", "").strip().lower()
        telefono = request.POST.get("telefono", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        if not nombre or not correo or not password:
            messages.error(request, "Nombre, correo y contraseña son obligatorios.")
            return render(request, "registro.html")

        if password != password_confirm:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, "registro.html")

        existe_correo = Usuario.objects.filter(Q(correo=correo)).exists()
        if existe_correo:
            messages.error(request, "Ya existe una cuenta con ese correo.")
            return render(request, "registro.html")

        usuario = Usuario.objects.create(
            nombre=nombre,
            apellido=apellido or None,
            telefono=telefono or None,
            correo=correo,
            password=make_password(password),
            rol="cliente",
        )
        request.session["usuario_id"] = usuario.id_usuario
        messages.success(request, "Cuenta creada correctamente.")
        return redirect("catalogo:lista")

    return render(request, "registro.html")


def restablecer(request):
    return render(request, "restablecer.html")

