from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()

class ReminderNotification(models.Model):
    INTERVAL_CHOICES = (
        ('7_days', '7 Days'),
        ('1_day', '1 Day'),
        ('12_hours', '12 Hours'),
    )
    
    # Generic foreign key fields
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    interval = models.CharField(max_length=20, choices=INTERVAL_CHOICES)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['content_type', 'object_id', 'interval', 'recipient']
        indexes = [
            models.Index(fields=['content_type', 'object_id', 'interval', 'recipient']),
        ]
    
    def __str__(self):
        return f"Reminder for {self.target} ({self.interval}) sent to {self.recipient} at {self.sent_at}"