from django.http import JsonResponse, HttpResponseNotFound
from django.core.handlers.wsgi import WSGIRequest

from ..base_plugin import BasePlugin


class YookassaPlugin(BasePlugin):
    """Yookassa payment into Saleor"""

    PLUGIN_NAME = " Plugin"
    PLUGIN_ID = "yookassa"
    DEFAULT_ACTIVE = True
    PLUGIN_DESCRIPTION = (
        "Yookassa payment into Saleor"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> JsonResponse:
        if path == "/webhook/yookassa":
            # do something with the request
            return JsonResponse(data={"paid": True})
        return JsonResponse(data={"paid": False})
