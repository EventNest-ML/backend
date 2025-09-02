from rest_framework import serializers
import uuid
from django.contrib.auth import get_user_model
from .models import Event, Invitation, Collaborator

User = get_user_model()

class CollaboratorSerializer(serializers.ModelSerializer):
    """Serializer for displaying collaborator details."""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Collaborator
        fields = ['username', 'role', 'joined_at']

class EventListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing events (summary view).
    """
    owner = serializers.StringRelatedField()

    class Meta:
        model = Event
        fields = ['id', 'name', 'date', 'location', 'owner']

class EventDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, retrieving, and updating a single event.
    """
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    collaborators = CollaboratorSerializer(source='collaborator_set', many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'name', 'date', 'location', 'notes', 'owner', 'collaborators']
        read_only_fields = ['id', 'owner', 'collaborators']

class InvitationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating and sending an invitation.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        event = self.context['event']
       
        # Check if user is already a collaborator
        if event.collaborators.filter(email=value).exists():
            raise serializers.ValidationError("This user is already a collaborator on this event.")
        # Check for a pending invitation
        if Invitation.objects.filter(event=event, email=value, status='PENDING').exists():
            invitation = Invitation.objects.get(event=event, email=value, status='PENDING')
            
            # if invitation is expired
            if invitation.is_valid():
                raise serializers.ValidationError("An invitation has already been sent to this email address and has not expired.")
            else:
                invitation.delete() # deletes invitation if it has expired so that another can be created!
        return value

class InvitationAcceptSerializer(serializers.Serializer):
    """
    Serializer to validate an invitation token.
    """
    token = serializers.UUIDField()