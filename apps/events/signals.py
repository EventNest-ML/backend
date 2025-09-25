# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invitation, Event
from .utils.email import send_invite_mail
from notifications.signals import notify
from apps.budgets.models import Budget
from djmoney.money import Money


@receiver(post_save, sender=Invitation)
def invitation_created_handler(sender, instance: Invitation, created, **kwargs):
    """
    Send invitation email when a new invitation is created
    """
    if created:
        try:
            invite_link = instance.get_full_invitation_url() 
            print("Generated invite link: ", invite_link, f'for user {instance.email}')
            
            send_invite_mail(
                invite_link=invite_link,
                email_addr=instance.email,
                event=instance.event
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send invitation email: {str(e)}")

# Example of connecting to other model signals
@receiver(post_save, sender=Event)
def handle_event_updated(sender, instance: Event, created, **kwargs):
    """
    Handle event creation - this creates notifications which then trigger WebSocket broadcast
    """
    if not created:
        print("Event Update...")
        sender = instance.collaborators.get(collaborator__role='ADMIN')
        recipients = instance.collaborators.exclude(collaborator__role='ADMIN')
        
        if recipients:
            for recipient in recipients:
                # The notification creation will automatically trigger the WebSocket broadcast
                notify.send(
                    sender=sender,
                    recipient=recipient,
                    verb='Event Updated',
                    action_object=instance,
                    description=f'"{instance.name}" event has been updated by {sender.get_full_name}',
                    data={
                        'event_id': instance.id,
                        'event_title': instance.name,
                        'notification_type': 'event_created',
                        'priority': 'normal'
                    }
                )


@receiver(post_save, sender=Event)
def create_event_budget(sender, instance, created, **kwargs):
    """Automatically create a disabled budget when an event is created"""
    if created:
        Budget.objects.create(
            event=instance,
            estimated_amount=Money(0, 'NGN'),
            is_enabled=False
        )