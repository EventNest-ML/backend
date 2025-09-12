"""
ASGI config for eventnest project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from .websocket_urls import websocket_urlpatterns
from .middleware import JWTAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventnest.settings.development")
print(os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventnest.settings.development"))

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket':JWTAuthMiddleware(URLRouter(websocket_urlpatterns))
})
