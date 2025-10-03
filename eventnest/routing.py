from channels.routing import URLRouter
from django.urls import path

from apps.budgets.routing import websocket_urlpatterns as budget_ws_urls
from apps.user_notifications.routing import websocket_urlpatterns as notifications_ws_urls

websocket_urlpatterns = [
    path('ws/budgets/', URLRouter(budget_ws_urls)),
    path('ws/notifications/', URLRouter(notifications_ws_urls)),
]