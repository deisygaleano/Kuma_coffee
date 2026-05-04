from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    imagen_file = forms.FileField(
        required=False,
        label="Foto del producto",
        widget=forms.ClearableFileInput(attrs={"accept": "image/*", "class": "admin-input"}),
    )

    class Meta:
        model = Producto
        fields = ["nombre", "precio", "categoria", "altura", "tostion", "descripcion", "slug"]
        widgets = {
            "nombre":      forms.TextInput(attrs={"class": "admin-input"}),
            "precio":      forms.NumberInput(attrs={"class": "admin-input"}),
            "categoria":   forms.Select(attrs={"class": "admin-select"}),
            "altura":      forms.Select(attrs={"class": "admin-select"}),
            "tostion":     forms.Select(attrs={"class": "admin-select"}),
            "descripcion": forms.TextInput(attrs={"class": "admin-input"}),
            "slug":        forms.TextInput(attrs={"class": "admin-input"}),
        }
        labels = {
            "nombre":      "Nombre",
            "precio":      "Precio",
            "categoria":   "Categoría",
            "altura":      "Altura",
            "tostion":     "Tostión",
            "descripcion": "Descripción",
            "slug":        "Slug (URL)",
        }