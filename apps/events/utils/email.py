from django.core.mail import send_mail
from django.conf import settings

def send_invite_mail(invite_link, email_addr, event):
    subject = f"Invitation for {event.name} collaboration"
    message = f"""Hello, there.
    {event.owner.firstname} is inviting you to be a collaborator in their upcomming {event.name} event.
    you can reach out to the owner of this event via {event.owner.email}
    please click the link below to join (Link expires the next 7 days):
    {invite_link}
    best regards. enventnest
    """

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email_addr],
        fail_silently=False
    )