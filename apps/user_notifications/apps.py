from django.apps import AppConfig
from django.contrib.auth import get_user_model



class NotificationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.user_notifications"

    def ready(self):
        import apps.user_notifications.signals
