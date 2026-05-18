from django import template

register = template.Library()


@register.filter
def peso_co(value):
    """Formatea un número como peso colombiano: puntos de miles, sin decimales.
    Ejemplo: 1500000 → $1.500.000
    """
    try:
        entero = int(round(float(value)))
        return f"{entero:,}".replace(",", ".")
    except (TypeError, ValueError):
        return value
