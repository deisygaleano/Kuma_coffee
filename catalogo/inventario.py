from catalogo.models import InventarioProducto


class StockInsuficienteError(Exception):
    def __init__(self, producto, solicitado, disponible):
        self.producto = producto
        self.solicitado = solicitado
        self.disponible = disponible
        super().__init__(
            f"Stock insuficiente para {producto.nombre}: "
            f"solicitado {solicitado}, disponible {disponible}"
        )


def asegurar_inventario(producto):
    inventario, _ = InventarioProducto.objects.get_or_create(
        producto=producto,
        defaults={
            "stock": producto.stock,
            "stock_minimo": producto.stock_minimo,
        },
    )
    return inventario


def stock_disponible(producto):
    inventario = asegurar_inventario(producto)
    return inventario.stock


def descontar_stock_lineas(lineas):
    """
    Descuenta stock por cada línea de pedido.
    Debe invocarse dentro de transaction.atomic().
    """
    lineas_lista = list(lineas)
    if not lineas_lista:
        return

    for linea in lineas_lista:
        asegurar_inventario(linea.producto)

    producto_ids = [linea.producto_id for linea in lineas_lista]
    inventarios = {
        inv.producto_id: inv
        for inv in InventarioProducto.objects.select_for_update().filter(
            producto_id__in=producto_ids
        )
    }

    for linea in lineas_lista:
        inventario = inventarios[linea.producto_id]
        if inventario.stock < linea.cantidad:
            raise StockInsuficienteError(
                linea.producto, linea.cantidad, inventario.stock
            )
        inventario.stock -= linea.cantidad
        inventario.save(update_fields=["stock"])
