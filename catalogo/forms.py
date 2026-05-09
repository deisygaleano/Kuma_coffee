from django import forms

from .models import InventarioProducto, Producto


class ProductoForm(forms.ModelForm):
    stock = forms.IntegerField(
        min_value=0,
        initial=0,
        label="Stock actual",
        widget=forms.NumberInput(attrs={"class": "admin-input", "min": 0}),
    )
    stock_minimo = forms.IntegerField(
        min_value=0,
        initial=5,
        label="Stock minimo",
        widget=forms.NumberInput(attrs={"class": "admin-input", "min": 0}),
    )
    imagen_file = forms.FileField(
        required=False,
        label="Foto del producto",
        widget=forms.ClearableFileInput(attrs={"accept": "image/*", "class": "admin-input"}),
    )

    class Meta:
        model = Producto
        fields = [
            "nombre",
            "precio",
            "categoria",
            "altura",
            "tostion",
            "descripcion",
            "slug",
        ]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "admin-input"}),
            "precio": forms.NumberInput(attrs={"class": "admin-input"}),
            "categoria": forms.Select(attrs={"class": "admin-select"}),
            "altura": forms.Select(attrs={"class": "admin-select"}),
            "tostion": forms.Select(attrs={"class": "admin-select"}),
            "descripcion": forms.TextInput(attrs={"class": "admin-input"}),
            "slug": forms.TextInput(attrs={"class": "admin-input"}),
        }
        labels = {
            "nombre": "Nombre",
            "precio": "Precio",
            "categoria": "Categoria",
            "altura": "Altura",
            "tostion": "Tostion",
            "descripcion": "Descripcion",
            "slug": "Slug (URL)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            inventario, _ = InventarioProducto.objects.get_or_create(
                producto=self.instance,
                defaults={
                    "stock": self.instance.stock,
                    "stock_minimo": self.instance.stock_minimo,
                },
            )
            self.fields["stock"].initial = inventario.stock
            self.fields["stock_minimo"].initial = inventario.stock_minimo
