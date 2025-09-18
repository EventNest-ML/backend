from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings


def send_invite_mail(invite_link, email_addr, event):
    """
    Send invitation email using HTML template
    """
   
    site_name = getattr(settings, 'SITE_NAME', 'EventNest')
    domain = getattr(settings, 'DOMAIN', 'localhost:8000')

    subject = f"Invitation for {event.name} collaboration"
    
    # Context for the template
    context = {
        'invite_link': invite_link,
        'event': event,
        'site_name': site_name,
        'domain': domain,
        'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
    }
    
    # Render HTML email
    html_message = render_to_string('event/invitation_email.html', context)
    
    # Create plain text version by stripping HTML
    plain_message = strip_tags(html_message)
    
    return send_mail(
        subject=subject,
        message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email_addr],
        html_message=html_message,
        fail_silently=False
    )