from django.urls import re_path
from .consumers import ExpenseCommentConsumer

websocket_urlpatterns = [
    re_path(r'expenses/(?P<expense_id>[^/]+)/comments/$', ExpenseCommentConsumer.as_asgi()),
]