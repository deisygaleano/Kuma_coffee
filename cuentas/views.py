import base64
import hashlib
import secrets
import urllib.parse

import requests as http_requests
from django.conf import settings as django_settings
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from .forms import CambiarPasswordForm, FotoUsuarioForm, LoginForm, RegistroForm, RestablecerPasswordForm
from .models import Usuario

_GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
_GOOGLE_SCOPES = "openid email profile"
_GOOGLE_FLOW_SESSION_KEY = "google_oauth_flows"


def _redirect_seguro(request):
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or ""
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("catalogo:lista")


def _eliminar_archivo_foto(usuario):
    if usuario.foto:
        usuario.foto.delete(save=False)


def _pkce_pair():
    """Genera (code_verifier, code_challenge) según RFC 7636 S256."""
    verifier = secrets.token_urlsafe(96)[:128]
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge


def _google_redirect_uri(request):
    configured_uri = getattr(django_settings, "GOOGLE_REDIRECT_URI", "")
    if configured_uri:
        return configured_uri
    return request.build_absolute_uri(reverse("cuentas:google_callback"))


def _google_login_host_canonico(request):
    configured_uri = getattr(django_settings, "GOOGLE_REDIRECT_URI", "")
    if not configured_uri:
        return None

    parsed_redirect = urllib.parse.urlparse(configured_uri)
    if not parsed_redirect.netloc or parsed_redirect.netloc == request.get_host():
        return None

    next_url = request.GET.get("next") or ""
    query = urllib.parse.urlencode({"next": next_url}) if next_url else ""
    path = reverse("cuentas:google_login")
    return urllib.parse.urlunparse(
        (
            parsed_redirect.scheme or request.scheme,
            parsed_redirect.netloc,
            path,
            "",
            query,
            "",
        )
    )


def _guardar_google_flow(request, state, code_verifier, redirect_uri, next_url=""):
    flows = request.session.get(_GOOGLE_FLOW_SESSION_KEY, {})
    flows[state] = {
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri,
        "next": next_url,
    }

    # Evita que la sesion crezca indefinidamente si el usuario intenta varias veces.
    if len(flows) > 5:
        for old_state in list(flows.keys())[:-5]:
            flows.pop(old_state, None)

    request.session[_GOOGLE_FLOW_SESSION_KEY] = flows
    request.session["google_oauth_state"] = state
    request.session["google_code_verifier"] = code_verifier


def login(request):
    form = LoginForm(request.POST or None)
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if request.method == "POST" and form.is_valid():
        correo = form.cleaned_data["correo"]
        password = form.cleaned_data["password"]
        usuarios = Usuario.objects.filter(correo__iexact=correo).order_by("-password", "id_usuario")
        usuario = next(
            (usuario for usuario in usuarios if usuario.password and check_password(password, usuario.password)),
            None,
        )

        if usuario:
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
        correo = form.cleaned_data["correo"]
        password_hash = make_password(form.cleaned_data["password"])
        usuarios = Usuario.objects.filter(correo__iexact=correo)
        usuarios.update(correo=correo, password=password_hash)
        messages.success(request, "Contrasena actualizada correctamente. Inicia sesion.")
        return redirect("cuentas:login")

    return render(request, "restablecer.html", {"form": form})


def cambiar_password(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        messages.error(request, "Debes iniciar sesion para cambiar tu contrasena.")
        return redirect("cuentas:login")

    usuario = Usuario.objects.filter(pk=usuario_id).first()
    if not usuario:
        request.session.pop("usuario_id", None)
        return redirect("cuentas:login")

    require_current_password = bool(usuario.password)
    form = CambiarPasswordForm(
        request.POST or None,
        require_current_password=require_current_password,
    )
    if request.method == "POST" and form.is_valid():
        if require_current_password and not check_password(form.cleaned_data["password_actual"], usuario.password):
            form.add_error("password_actual", "La contrasena actual es incorrecta.")
        else:
            usuario.password = make_password(form.cleaned_data["password_nueva"])
            usuario.save(update_fields=["password"])
            messages.success(request, "Contrasena actualizada correctamente.")
            return redirect("catalogo:lista")

    return render(request, "cambiar_password.html", {"form": form})


@require_POST
def actualizar_foto(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        messages.error(request, "Debes iniciar sesion para actualizar tu foto.")
        return redirect("cuentas:login")

    usuario = Usuario.objects.filter(pk=usuario_id).first()
    if not usuario:
        request.session.pop("usuario_id", None)
        messages.error(request, "La sesion no es valida. Inicia sesion de nuevo.")
        return redirect("cuentas:login")

    if request.POST.get("accion") == "eliminar":
        _eliminar_archivo_foto(usuario)
        usuario.foto = None
        usuario.save(update_fields=["foto"])
        messages.success(request, "Foto de perfil eliminada.")
        return _redirect_seguro(request)

    form = FotoUsuarioForm(request.POST, request.FILES)
    if form.is_valid():
        _eliminar_archivo_foto(usuario)
        usuario.foto = form.cleaned_data["foto"]
        usuario.save(update_fields=["foto"])
        messages.success(request, "Foto de perfil actualizada.")
    else:
        messages.error(request, form.errors.get("foto", ["No se pudo actualizar la foto."])[0])

    return _redirect_seguro(request)


@require_POST
def logout(request):
    request.session.pop("usuario_id", None)
    messages.success(request, "Sesion cerrada correctamente.")
    return redirect("inicio")


def google_login(request):
    canonical_login_url = _google_login_host_canonico(request)
    if canonical_login_url:
        return redirect(canonical_login_url)

    code_verifier, code_challenge = _pkce_pair()
    state = secrets.token_urlsafe(32)
    redirect_uri = _google_redirect_uri(request)
    next_url = request.GET.get("next") or ""

    params = {
        "client_id": django_settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": _GOOGLE_SCOPES,
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    _guardar_google_flow(request, state, code_verifier, redirect_uri, next_url)
    return redirect(f"{_GOOGLE_AUTH_URI}?{urllib.parse.urlencode(params)}")


def google_callback(request):
    state_param = request.GET.get("state")
    code = request.GET.get("code")
    flows = request.session.get(_GOOGLE_FLOW_SESSION_KEY, {})
    flow = flows.pop(state_param, None) if state_param else None
    if state_param and _GOOGLE_FLOW_SESSION_KEY in request.session:
        request.session[_GOOGLE_FLOW_SESSION_KEY] = flows
        request.session.modified = True

    if not flow or not code:
        messages.error(request, "Sesion OAuth invalida. Intenta de nuevo.")
        return redirect("cuentas:login")

    code_verifier = flow.get("code_verifier")
    redirect_uri = flow.get("redirect_uri") or _google_redirect_uri(request)
    next_url = flow.get("next") or ""

    try:
        token_resp = http_requests.post(
            _GOOGLE_TOKEN_URI,
            data={
                "client_id": django_settings.GOOGLE_CLIENT_ID,
                "client_secret": django_settings.GOOGLE_CLIENT_SECRET,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
            timeout=10,
        )
        token_data = token_resp.json()
        if "error" in token_data:
            raise ValueError(token_data.get("error_description", token_data["error"]))

        id_info = id_token.verify_oauth2_token(
            token_data["id_token"],
            google_requests.Request(),
            django_settings.GOOGLE_CLIENT_ID,
        )
    except Exception:
        messages.error(request, "No se pudo completar el inicio de sesion con Google.")
        return redirect("cuentas:login")

    google_sub = id_info.get("sub")
    email = (id_info.get("email") or "").strip().lower()
    nombre = id_info.get("given_name") or email.split("@")[0]
    apellido = id_info.get("family_name") or None

    if not google_sub or not email:
        messages.error(request, "Google no entrego la informacion necesaria para iniciar sesion.")
        return redirect("cuentas:login")

    usuario = Usuario.objects.filter(google_id=google_sub).first()
    if not usuario:
        usuario = Usuario.objects.filter(correo__iexact=email).first()
        if usuario:
            if usuario.google_id and usuario.google_id != google_sub:
                messages.error(request, "Este correo ya esta vinculado a otra cuenta de Google.")
                return redirect("cuentas:login")
            if not usuario.google_id:
                usuario.google_id = google_sub
                usuario.save(update_fields=["google_id"])
        else:
            usuario = Usuario.objects.create(
                nombre=nombre,
                apellido=apellido,
                correo=email,
                google_id=google_sub,
                password=None,
                rol="cliente",
            )

    request.session["usuario_id"] = usuario.id_usuario
    messages.success(request, f"Bienvenido, {usuario.nombre}.")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("catalogo:lista")
