import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Usuario


class FotoUsuarioForm(forms.Form):
    foto = forms.FileField(
        label="Foto de perfil",
        required=True,
        widget=forms.FileInput(
            attrs={
                "accept": "image/jpeg,image/png,image/webp",
                "class": "usuario-modal__file-input",
            }
        ),
    )

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if not foto:
            raise forms.ValidationError("Debes seleccionar una imagen.")

        extensiones_permitidas = (".jpg", ".jpeg", ".png", ".webp")
        nombre = (foto.name or "").lower()
        extension_valida = any(nombre.endswith(ext) for ext in extensiones_permitidas)

        tipos_permitidos = {
            "image/jpeg",
            "image/jpg",
            "image/pjpeg",
            "image/png",
            "image/x-png",
            "image/webp",
        }
        tipo = (foto.content_type or "").lower()
        tipo_valido = not tipo or tipo in tipos_permitidos
        if not extension_valida and not tipo_valido:
            raise forms.ValidationError("Sube una imagen JPG, PNG o WEBP.")

        if foto.size > 2 * 1024 * 1024:
            raise forms.ValidationError("La imagen no debe superar 2 MB.")

        return foto


class AuthBaseForm(forms.Form):
    def _aplicar_clase(self):
        for field in self.fields.values():
            css_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css_class} auth-input".strip()


class LoginForm(AuthBaseForm):
    correo = forms.EmailField(
        label="Correo",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Contraseña",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_clase()

    def clean_correo(self):
        return self.cleaned_data["correo"].strip().lower()


class RegistroForm(AuthBaseForm):
    nombre = forms.CharField(label="Nombre", min_length=2, max_length=32)
    apellido = forms.CharField(label="Apellido", min_length=2, max_length=32, required=False)
    correo = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    telefono = forms.CharField(label="Teléfono", max_length=20, required=False)
    password = forms.CharField(
        label="Contraseña",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="Confirmar contraseña",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_clase()

    def clean_nombre(self):
        return self.cleaned_data["nombre"].strip()

    def clean_apellido(self):
        return self.cleaned_data["apellido"].strip()

    def clean_correo(self):
        correo = self.cleaned_data["correo"].strip().lower()
        if Usuario.objects.filter(correo__iexact=correo).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data["telefono"].strip()
        if telefono and not re.fullmatch(r"\+?\d{7,20}", telefono):
            raise forms.ValidationError("Ingresa un teléfono válido entre 7 y 20 dígitos.")
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Las contraseñas no coinciden.")

        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error("password", error)

        return cleaned_data


class RestablecerPasswordForm(AuthBaseForm):
    correo = forms.EmailField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Nueva contraseña",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="Confirmar nueva contraseña",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_clase()

    def clean_correo(self):
        correo = self.cleaned_data["correo"].strip().lower()
        if not Usuario.objects.filter(correo__iexact=correo).exists():
            raise forms.ValidationError("No existe una cuenta registrada con ese correo.")
        return correo

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Las contraseñas no coinciden.")

        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error("password", error)

        return cleaned_data

class CambiarPasswordForm(AuthBaseForm):
    password_actual = forms.CharField(
        label="Contraseña actual",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    password_nueva = forms.CharField(
        label="Nueva contraseña",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_nueva_confirm = forms.CharField(
        label="Confirmar nueva contraseña",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, require_current_password=True, **kwargs):
        self.require_current_password = require_current_password
        super().__init__(*args, **kwargs)
        self.fields["password_actual"].required = require_current_password
        if not require_current_password:
            self.fields["password_actual"].help_text = "No necesitas contraseña actual para configurar tu primera contraseña."
        self._aplicar_clase()

    def clean(self):
        cleaned_data = super().clean()
        password_nueva = cleaned_data.get("password_nueva")
        password_nueva_confirm = cleaned_data.get("password_nueva_confirm")

        if password_nueva and password_nueva_confirm and password_nueva != password_nueva_confirm:
            self.add_error("password_nueva_confirm", "Las contraseñas no coinciden.")

        if password_nueva:
            try:
                validate_password(password_nueva)
            except ValidationError as error:
                self.add_error("password_nueva", error)

        return cleaned_data
