# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Invitation
from .utils.email import send_invite_mail

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