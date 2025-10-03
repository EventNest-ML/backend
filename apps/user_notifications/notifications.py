from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from notifications.signals import notify
from datetime import datetime


User = get_user_model()

def format_field_value(field, value):
    """Format field values for email display"""
    if field == 'due_date' and value:
        try:
            if isinstance(value, str):
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return value.strftime("%B %d, %Y at %I:%M %p")
        except:
            return str(value)
    elif field == 'status':
        return value.replace('_', ' ').title()
    elif field in ['title', 'description']:
        return value
    else:
        return str(value)

# Notification functions
def send_task_assignment_notification(task):
    """Send notification when a task is assigned"""
    recipient = task.assignee
    actor = task.created_by
    message = f"You have been assigned a new task: {task.title} for event {task.event.name}"
    
    # Store notification
    notify.send(
        sender=actor,
        recipient=recipient,
        verb='Task Assigned',
        target=task,
        description=message
    )
    
    # Send email
    context = {
        'site_name': settings.SITE_NAME,
        'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
        'domain': getattr(settings, 'DOMAIN', 'localhost:8000'),
        'user': recipient,
        'task_title': task.title,
        'event_name': task.event.name,
        'due_date': task.due_date,
        'task_id': task.id,
        'description': task.description or 'No description'
    }
    subject = f"New Task Assignment: {task.title}"
    html_message = render_to_string('notifications/task_assignment.html', context)
    
    send_mail(
        subject,
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient.email],
        html_message=html_message,
        fail_silently=True
    )

def send_expense_assignment_notification(expense):
    """Send notification when a task is assigned"""
    recipient = expense.assignee.user
    actor = expense.budget.event.owner
    print("Actorrr: ", actor)
    print("Recipient: ", recipient)
    message = f"You have been assigned a new expense: {expense.name} for event {expense.budget.event.name}"
    
    # Store notification
    notify.send(
        sender=actor,
        recipient=recipient,
        verb='Expense Assigned',
        target=expense,
        description=message
    )
    
    # Send email
    context = {
        'site_name': settings.SITE_NAME,
        'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
        'domain': getattr(settings, 'DOMAIN', 'localhost:8000'),
        'user': recipient,
        'expense_id': expense.id,
        'expense_name': expense.name,
        'event_id': expense.budget.event.id,
        'event_name': expense.budget.event.name,
        'due_date': expense.due_date,
        'description': expense.description or 'No description'
    }
    subject = f"New Expense Assignment: {expense.name}"
    html_message = render_to_string('notifications/expense_assignment.html', context)
    
    send_mail(
        subject,
        html_message,
        settings.DEFAULT_FROM_EMAIL,
        [recipient.email],
        html_message=html_message,
        fail_silently=True
    )

def send_task_update_notification(task, updated_fields, actor):
    """Send notification when a task is updated"""
    recipient = task.assignee
    changes_list = [
        f"{field.replace('_', ' ').title()}: {format_field_value(field, getattr(task, field))}"
        for field in updated_fields
    ]
    # field_changes = [f"{field}: {getattr(task, field)}" for field in updated_fields]
    field_changes = ", ".join([f"{field}: {getattr(task, field)}" for field in updated_fields])
    message = f"Task '{task.title}' updated: {field_changes}"
    
    # Store notification
    notify.send(
        sender=actor,
        recipient=recipient,
        verb='Task Updated',
        target=task,
        description=message
    )
    
    # Send email for significant updates
    if any(field in updated_fields for field in ['status', 'due_date', 'assignee']):
        context = {
            'site_name': settings.SITE_NAME,
            'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
            'domain': getattr(settings, 'DOMAIN', 'localhost:8000'),
            'user': recipient,
            'task_title': task.title,
            'task_id': task.id,
            'event_name': task.event.name,
            'changes': changes_list
        }
        subject = f"Task Update: {task.title}"
        html_message = render_to_string('notifications/task_update.html', context)
        
        send_mail(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email],
            html_message=html_message,
            fail_silently=True
        )

def send_expense_update_notification(expense, updated_fields, actor):
    """Send notification when an expense is updated"""
    recipient = expense.assignee.user
    field_changes = ", ".join([f"{field}: {getattr(expense, field)}" for field in updated_fields])
    message = f"Expense '{expense.name}' updated: {field_changes}"
    
    # Store notification
    notify.send(
        sender=actor,
        recipient=recipient,
        verb='Expense Updated',
        target=expense,
        description=message
    )
    
    # Send email for significant updates
    if any(field in updated_fields for field in ['status', 'actual_cost', 'due_date']):
        context = {
            'site_name': settings.SITE_NAME,
            'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
            'domain': getattr(settings, 'DOMAIN', 'localhost:8000'),
            'user': recipient,
            'expense_name': expense.name,
            'expense_id': expense.id,
            'event_name': expense.budget.event.name,
            'changes': field_changes
        }
        subject = f"Expense Update: {expense.name}"
        html_message = render_to_string('notifications/expense_update.html', context)
        
        send_mail(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient.email],
            html_message=html_message,
            fail_silently=True
        )

def send_event_update_notification(event, updated_fields, actor):
    """Send notification when an event is updated"""
    recipients = User.objects.filter(
        id__in=event.collaborators.values_list('id', flat=True)
    )
    field_changes = ", ".join([f"{field}: {getattr(event, field)}" for field in updated_fields])
    message = f"Event '{event.name}' updated: {field_changes}"
    
    for recipient in recipients:
        # Store notification
        notify.send(
            sender=actor,
            recipient=recipient,
            verb='Event Updated',
            target=event,
            description=message
        )
        
        # Send email for significant updates
        if any(field in updated_fields for field in ['status', 'start_date', 'end_date', 'location']):
            context = {
                'site_name': settings.SITE_NAME,
                'protocol': 'https' if getattr(settings, 'USE_HTTPS', False) else 'http',
                'domain': getattr(settings, 'DOMAIN', 'localhost:8000'),
                'user': recipient,
                'event_name': event.name,
                'event_id': event.id,
                'changes': field_changes
            }
            subject = f"Event Update: {event.name}"
            html_message = render_to_string('notifications/event_update.html', context)
            
            send_mail(
                subject,
                html_message,
                settings.DEFAULT_FROM_EMAIL,
                [recipient.email],
                html_message=html_message,
                fail_silently=True
            )



