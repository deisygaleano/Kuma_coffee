from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class DescartarMensajesNoMostradosMiddleware(MiddlewareMixin):
    """Elimina mensajes flash que la plantilla no mostró para que no reaparezcan."""

    def process_response(self, request, response):
        storage = messages.get_messages(request)
        if not storage.used:
            list(storage)
        return response
