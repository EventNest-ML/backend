from celery import shared_task
from datetime import timedelta
from notifications.signals import notify
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from django.template.loader import render_to_string
from django.contrib.contenttypes.models import ContentType
from apps.user_notifications.models import ReminderNotification
from apps.tasks.models import Task
from apps.budgets.models import Expense
import datetime


@shared_task
def send_due_reminders():
    """Send reminders for objects nearing their due date - only for the closest interval"""
    
    # Intervals ordered from furthest to closest
    reminder_intervals = [
        ('7_days', timedelta(days=7)),
        ('1_day', timedelta(days=1)),
        ('12_hours', timedelta(hours=12)),
    ]
    
    model_configs = {
        'Task': {
            'model': Task,
            'status_field': 'status',
            'status_values': ['TODO', 'IN_PROGRESS'],
            'recipient_field': 'assignee',
            'title_field': 'title',
            'event_field': 'event.name',
            'verb': 'Task Due Reminder',
            'template': 'notifications/task_reminder.html',
            'subject_template': 'Task Reminder: {title}',
        },
        'Expense': {
            'model': Expense,
            'status_field': 'status',
            'status_values': ['pending'],
            'recipient_field': 'assignee.user',
            'title_field': 'name',
            'event_field': 'budget.event.name',
            'verb': 'Expense Due Reminder',
            'template': 'notifications/expense_reminder.html',
            'subject_template': 'Expense Reminder: {title}',
        },
    }
    
    now = timezone.now()
    
    for config in model_configs.values():
        model = config['model']
        content_type = ContentType.objects.get_for_model(model)
        
        # Get all objects that are due in the future, not complete, and have a non-null due_date
        filter_kwargs = {
            'due_date__gt': now,
            f"{config['status_field']}__in": config['status_values'],
            'due_date__isnull': False,  # Exclude null due_date
        }
        
        objects = model.objects.filter(**filter_kwargs)
        
        for obj in objects:
            # Double-check due_date (safeguard)
            if not obj.due_date:
                continue
            
            # Get recipient dynamically
            recipient = obj
            for field in config['recipient_field'].split('.'):
                recipient = getattr(recipient, field)

            # Convert due_date to datetime if it's a date
            if isinstance(obj.due_date, datetime.date) and not isinstance(obj.due_date, datetime.datetime):
                due_datetime = datetime.datetime.combine(obj.due_date, datetime.time(0, 0), tzinfo=timezone.get_current_timezone())
            else:
                due_datetime = obj.due_date
            
            # Calculate time until due
            time_until_due = due_datetime - now
            
            # Find the closest matching interval that hasn't been sent yet
            matched_interval = None
            for interval_name, interval_duration in reminder_intervals:
                # Check if this interval matches (within a small tolerance window)
                tolerance = timedelta(hours=1)  # Allow 1 hour tolerance
                
                if abs(time_until_due - interval_duration) <= tolerance:
                    # Check if we already sent this interval reminder
                    already_sent = ReminderNotification.objects.filter(
                        content_type=content_type,
                        object_id=obj.pk,
                        interval=interval_name,
                        recipient=recipient
                    ).exists()
                    
                    if not already_sent:
                        matched_interval = (interval_name, interval_duration)
                        break
            
            # Send notification only if we found a matching interval
            if matched_interval:
                interval_name, interval_duration = matched_interval
                
                # Get title and event name dynamically
                title = getattr(obj, config['title_field'])
                event_name = obj
                for field in config['event_field'].split('.'):
                    event_name = getattr(event_name, field)
                
                # Format time remaining
                if interval_duration.days > 0:
                    time_str = f"{interval_duration.days} day(s)"
                else:
                    hours = interval_duration.seconds // 3600
                    time_str = f"{hours} hour(s)"
                
                message = f"Reminder: {config['model'].__name__} '{title}' is due in {time_str}"
                
                # Store in-app notification
                notify.send(
                    sender=recipient,
                    recipient=recipient,
                    verb=config['verb'],
                    target=obj,
                    description=message
                )
                
                # Send email
                context = {
                    'site_name': getattr(settings, 'SITE_NAME', 'Event Management'),
                    'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
                    'domain': getattr(settings, 'DOMAIN', 'localhost:8000'),
                    'user': recipient,
                    f"{config['model'].__name__.lower()}_title": title,
                    'event_name': event_name,
                    'due_date': obj.due_date,
                    'time_remaining': time_str
                }
                subject = config['subject_template'].format(title=title)
                html_message = render_to_string(config['template'], context)
                
                send_mail(
                    subject,
                    html_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [recipient.email],
                    html_message=html_message,
                    fail_silently=True
                )
                
                # Record the sent reminder
                ReminderNotification.objects.create(
                    content_type=content_type,
                    object_id=obj.pk,
                    recipient=recipient,
                    interval=interval_name
                )
    
    return f"Reminder check completed at {timezone.now()}"
