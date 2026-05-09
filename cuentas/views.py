from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import LoginForm, RegistroForm, RestablecerPasswordForm
from .models import Usuario


def login(request):
    form = LoginForm(request.POST or None)
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if request.method == "POST" and form.is_valid():
        correo = form.cleaned_data["correo"]
        password = form.cleaned_data["password"]
        usuario = Usuario.objects.filter(correo=correo).first()

        if usuario and check_password(password, usuario.password):
            request.session["usuario_id"] = usuario.id_usuario
            messages.success(request, f"Bienvenido, {usuario.nombre}.")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect("catalogo:lista")

        messages.error(request, "Credenciales invalidas.")

    return render(request, "login.html", {"form": form, "next": next_url})


def registro(request):
    form = RegistroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = Usuario.objects.create(
            nombre=form.cleaned_data["nombre"],
            apellido=form.cleaned_data["apellido"] or None,
            telefono=form.cleaned_data["telefono"] or None,
            correo=form.cleaned_data["correo"],
            password=make_password(form.cleaned_data["password"]),
            rol="cliente",
        )
        request.session["usuario_id"] = usuario.id_usuario
        messages.success(request, f"Cuenta creada correctamente. Bienvenido, {usuario.nombre}.")
        return redirect("catalogo:lista")

    return render(request, "registro.html", {"form": form})


def restablecer(request):
    form = RestablecerPasswordForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = Usuario.objects.get(correo=form.cleaned_data["correo"])
        usuario.password = make_password(form.cleaned_data["password"])
        usuario.save(update_fields=["password"])
        messages.success(request, "Contrasena actualizada correctamente. Inicia sesion.")
        return redirect("cuentas:login")

    return render(request, "restablecer.html", {"form": form})


@require_POST
def logout(request):
    request.session.pop("usuario_id", None)
    messages.success(request, "Sesion cerrada correctamente.")
    return redirect("inicio")
