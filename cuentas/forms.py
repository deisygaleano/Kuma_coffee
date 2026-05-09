import re

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Usuario


class AuthBaseForm(forms.Form):
    def _aplicar_clase(self):
        for field in self.fields.values():
            css_class = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = f"{css_class} auth-input".strip()


class LoginForm(AuthBaseForm):
    correo = forms.EmailField(
        label="Correo",
        max_length=32,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Contrasena",
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
        label="Correo electronico",
        max_length=32,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    telefono = forms.CharField(label="Telefono", max_length=20, required=False)
    password = forms.CharField(
        label="Contrasena",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="Confirmar contrasena",
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
        if Usuario.objects.filter(correo=correo).exists():
            raise forms.ValidationError("Ya existe una cuenta con ese correo.")
        return correo

    def clean_telefono(self):
        telefono = self.cleaned_data["telefono"].strip()
        if telefono and not re.fullmatch(r"\+?\d{7,20}", telefono):
            raise forms.ValidationError("Ingresa un telefono valido entre 7 y 20 digitos.")
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Las contrasenas no coinciden.")

        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error("password", error)

        return cleaned_data


class RestablecerPasswordForm(AuthBaseForm):
    correo = forms.EmailField(
        label="Correo electronico",
        max_length=32,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Nueva contrasena",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="Confirmar nueva contrasena",
        max_length=128,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aplicar_clase()

    def clean_correo(self):
        correo = self.cleaned_data["correo"].strip().lower()
        if not Usuario.objects.filter(correo=correo).exists():
            raise forms.ValidationError("No existe una cuenta registrada con ese correo.")
        return correo

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "Las contrasenas no coinciden.")

        if password:
            try:
                validate_password(password)
            except ValidationError as error:
                self.add_error("password", error)

        return cleaned_data
