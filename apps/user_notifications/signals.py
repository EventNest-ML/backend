from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from notifications.models import Notification
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Notification)
def broadcast_notification_to_websocket(sender, instance, created, **kwargs):
    """
    Generic signal that broadcasts any new notification to WebSocket
    This handles ALL notifications regardless of the source model
    """
    if created:
        try:
            # Get the channel layer
            channel_layer = get_channel_layer()
            
            recipient = instance.recipient 
            group_name = f"notifications_{recipient.id}"
            
            logger.info(f"Broadcasting notification {instance.id} to user {recipient.id}")
            
            # Send notification to the user's WebSocket group
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "new_notification_message",
                    "notification_id": instance.id,
                }
            )

            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "fetch_notification_messages",
                }
            )

            
        except Exception as e:
            logger.error(f"Error broadcasting notification {instance.id}: {str(e)}")



