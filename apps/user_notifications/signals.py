from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from notifications.models import Notification
import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .notifications import (
    send_event_update_notification,
    send_expense_update_notification,
    send_task_assignment_notification,
    send_task_update_notification,
    send_expense_assignment_notification
)
from ..events.models import Event
from ..tasks.models import Task
from ..budgets.models import Expense


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



@receiver(pre_save, sender=Task)
def track_task_changes(sender, instance, **kwargs):
    if instance.pk:
        old_task = Task.objects.get(pk=instance.pk)
        updated_fields = []
        for field in ['title', 'description', 'due_date', 'status', 'assignee']:
            if getattr(old_task, field) != getattr(instance, field):
                updated_fields.append(field)
        instance._updated_fields = updated_fields


@receiver(post_save, sender=Task)
def handle_task_save(sender, instance, created, **kwargs):
    if created:
        send_task_assignment_notification(instance)
    elif hasattr(instance, '_updated_fields') and instance._updated_fields:
        send_task_update_notification(instance, instance._updated_fields, instance.created_by)


@receiver(pre_save, sender=Expense)
def track_expense_changes(sender, instance, **kwargs):
    if instance.pk:
        old_expense = Expense.objects.get(pk=instance.pk)
        updated_fields = []
        for field in ['name', 'description', 'estimated_cost', 'actual_cost', 'status', 'due_date']:
            if getattr(old_expense, field) != getattr(instance, field):
                updated_fields.append(field)
        instance._updated_fields = updated_fields
        


@receiver(post_save, sender=Expense)
def handle_expense_save(sender, instance, created, **kwargs):
    if hasattr(instance, '_updated_fields') and instance._updated_fields:
        send_expense_update_notification(instance, instance._updated_fields, instance.assignee.user)
    elif created:
        send_expense_assignment_notification(instance)


@receiver(pre_save, sender=Event)
def track_event_changes(sender, instance, **kwargs):
    if instance.pk:
        old_event = Event.objects.get(pk=instance.pk)
        updated_fields = []
        for field in ['name', 'type', 'date', 'location', 'status']:
            if getattr(old_event, field) != getattr(instance, field):
                updated_fields.append(field)
        instance._updated_fields = updated_fields


@receiver(post_save, sender=Event)
def handle_event_save(sender, instance, created, **kwargs):
    if hasattr(instance, '_updated_fields') and instance._updated_fields:
        send_event_update_notification(instance, instance._updated_fields, instance.updated_by)


