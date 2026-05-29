# Generated manually for correo length normalization.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cuentas", "0003_usuario_foto"),
    ]

    operations = [
        migrations.AlterField(
            model_name="usuario",
            name="correo",
            field=models.EmailField(max_length=254),
        ),
    ]
