import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class TimeStampedUUIDModel(models.Model):
    pkid = models.BigAutoField(primary_key=True, editable=True)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract =True


class Event(TimeStampedUUIDModel):
    name = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_events')

    def __str__(self):
        return self.name
