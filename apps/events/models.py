import uuid
from datetime import timedelta
from django.utils import timezone
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
    """
    Represents an event created by a user.
    """
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_events'
    )
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=200)
    date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    # audit fields
    updated_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_events"
    )
    collaborators = models.ManyToManyField(
        User,
        through='Collaborator',
        related_name='events_collaborating'
    )

    def __str__(self):
        return self.name

class Collaborator(models.Model):
    """
    Acts as an intermediary model to manage collaborators for an event.
    """
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        COLLABORATOR = 'COLLABORATOR', 'Collaborator'

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.COLLABORATOR)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event') # Ensures a user can only join an event once

    def __str__(self):
        return f"{self.user} - {self.event.name}"

class Invitation(models.Model):
    """
    Stores invitation records sent by event owners.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        DECLINED = 'DECLINED', 'Declined'

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='invitations')
    email = models.EmailField()
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=48)
        super().save(*args, **kwargs)

    def is_valid(self):
        return self.expires_at > timezone.now() #shows if the invitation link has expired or not
    

    def __str__(self):
        return f"Invitation for {self.email} to {self.event.name}"
