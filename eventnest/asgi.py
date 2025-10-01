"""
ASGI config for eventnest project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

# Set the default settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventnest.settings.development")
print(os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eventnest.settings.development"))

# Initialize Django
django.setup()

# Import after django.setup() to avoid AppRegistryNotReady
from .routing import websocket_urlpatterns
from .middleware import JWTAuthMiddleware

# Get the ASGI application for HTTP
django_asgi_app = get_asgi_application()

# Define the ASGI application
application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': JWTAuthMiddleware(URLRouter(websocket_urlpatterns))
})