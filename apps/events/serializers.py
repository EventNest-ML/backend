from rest_framework import serializers
import uuid
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Event, Invitation, Collaborator
from ..contacts.models import Contact

User = get_user_model()

class CollaboratorSerializer(serializers.ModelSerializer):
    """Serializer for displaying collaborator details."""
    fullname = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Collaborator
        fields = ['id','fullname','email','role', 'joined_at']

class EventListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing events (summary view).
    """
    owner = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Event
        fields = ['id', 'name', 'type', 'location', 'start_date', 'end_date', 'owner']

class EventDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, retrieving, and updating a single event.
    """
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    updated_by = serializers.HiddenField(default=serializers.CurrentUserDefault())
    collaborators = CollaboratorSerializer(source='collaborator_set', many=True, read_only=True)
    budget_id = serializers.CharField(source='budget.id', read_only=True)
    budget_amount = serializers.DecimalField(
        max_digits=14, 
        decimal_places=2, 
        write_only=True,
        required=False,
        allow_null=True,
        default=0,
        help_text="Initial budget amount for the event in NGN"
    )

    class Meta:
        model = Event
        fields = fields = ['id', 'name', 'location', 'type', 'notes', 'owner', 'start_date', 'end_date', 'updated_by', 'collaborators', 'budget_id', 'budget_amount']
        read_only_fields = ['id', 'owner', 'updated_by', 'collaborators', 'budget_id']
    
    def create(self, validated_data):
        # Extract budget_amount (won't be saved to Event model)
        budget_amount = validated_data.pop('budget_amount', 0)
        print("Budget Amount:", budget_amount)
        
        # Create the Event instance WITHOUT saving yet
        event = Event(**validated_data)
        
        # Store budget amount on the instance BEFORE saving
        event._budget_amount = budget_amount
        print("Budget amount stored on event instance:", event._budget_amount)
        
        # Now save - this triggers the signal with _budget_amount available
        event.save()
        print("Event saved:", event.id)
        
        return event

    def validate(self, data):
        request = self.context.get("request")
        if request and request.method not in ("POST", "PUT", "PATCH"):
            # Skip validation on non-create/update operations (like GET, DELETE)
            return data

        now = timezone.now()
        start_date = data.get("start_date", getattr(self.instance, "start_date", None))
        end_date = data.get("end_date", getattr(self.instance, "end_date", None))
        status = data.get("status", getattr(self.instance, "status", None))

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date cannot be later than end date.")

        if status == "ongoing" and end_date and end_date < now:
            raise serializers.ValidationError("An event with an end date in the past cannot be marked as ongoing.")

        if status == "completed" and end_date and end_date >= now:
            raise serializers.ValidationError("An event that has not ended cannot be marked as completed.")

        return data
    
class InvitationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating and sending an invitation.
    """
    email = serializers.EmailField(required=False)
    contact_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        event = self.context['event']
        email = attrs.get("email")
        contact_id = attrs.get("contact_id")
        request = self.context.get("request")

        if not email and not contact_id:
            raise serializers.ValidationError("Either email or contact_id is required.")
        

        # Resolve email if contact_id is provided
        if contact_id:
            try:
                contact = Contact.objects.get(id=contact_id, owner=request.user)
                attrs["email"] = contact.email
            except Contact.DoesNotExist:
                raise serializers.ValidationError({"contact_id": "Invalid contact_id."})
            

        # Use resolved email for further checks
        email = attrs["email"]
            
       
        # Check if user is already a collaborator
        if event.collaborators.filter(email=email).exists() or event.invitations.filter(email=email, status="ACCEPTED").exists():
            raise serializers.ValidationError("This user is already a collaborator on this event.")
        
        # Check for existing pending invitation
        pending_invite = Invitation.objects.filter(event=event, email=email, status="PENDING").first()
        if pending_invite:
            if pending_invite.is_valid():
                raise serializers.ValidationError("An invitation has already been sent to this email address and has not expired.")
            else:
                pending_invite.delete()  # remove expired invite

        print("***********attrs: ", attrs)

        return attrs

# class InvitationAcceptSerializer(serializers.Serializer):
#     """
#     Serializer to validate an invitation token.
#     """
#     token = serializers.UUIDField()

class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    action = serializers.ChoiceField(
        choices=[("accept", "Accept"), ("decline", "Decline")],
        default="accept"
    )



