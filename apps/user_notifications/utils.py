from notifications.signals import notify

def notify_multiple_users(sender, recipients, verb, description, target=None):
    for recipient in recipients:
        notify.send(
            sender=sender,
            recipient=recipient,
            verb=verb,
            description=description,
            target=target,
        )