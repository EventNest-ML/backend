# events/views.py

from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .models import Event, Invitation, Collaborator
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    InvitationCreateSerializer,
    InvitationAcceptSerializer
)
from .permissions import IsEventOwnerOrCollaboratorReadOnly
from .utils.email import send_invite_mail


# --- Event Management Views ---


class EventListCreateAPIView(APIView):
    """
    API view to list all events for the current user or create a new one.
    Corresponds to User Stories 2a and 2b.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # List events where the user is either the owner or a collaborator
        events = Event.objects.filter(owner=request.user) | Event.objects.filter(collaborators=request.user)
        serializer = EventListSerializer(events.distinct(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(request_body=EventDetailSerializer)
    def post(self, request, *args, **kwargs):
        # Create a new event
        serializer = EventDetailSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            event = serializer.save()
            # The creator automatically becomes an 'Admin' collaborator
            Collaborator.objects.create(user=request.user, event=event, role=Collaborator.Role.ADMIN)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventDetailAPIView(APIView):
    """
    API view to retrieve, update, or delete a specific event instance.
    Corresponds to User Story 2c.
    """
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrCollaboratorReadOnly]
    

    def get_object(self, id):
        event = get_object_or_404(Event, id=id)
        self.check_object_permissions(self.request, event)
        return event

    def get(self, request, id, *args, **kwargs):
        event = self.get_object(id)
        serializer = EventDetailSerializer(event)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=EventDetailSerializer)
    def put(self, request, id, *args, **kwargs):
        event = self.get_object(id)
        serializer = EventDetailSerializer(event, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=EventDetailSerializer)
    def patch(self, request, id, *args, **kwargs):
        """Partial update (only some fields can be sent)."""
        event = self.get_object(id)
        serializer = EventDetailSerializer(event, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, *args, **kwargs):
        event = self.get_object(id)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# --- Invitation Management Views ---

class InvitationCreateAPIView(APIView):
    """
    Creates and sends an invitation for an event.
    Corresponds to User Story 3a.
    """
    permission_classes = [permissions.IsAuthenticated, IsEventOwnerOrCollaboratorReadOnly]

    @swagger_auto_schema(request_body=InvitationCreateSerializer)
    def post(self, request, id, *args, **kwargs):
        event = get_object_or_404(Event, id=id)
        self.check_object_permissions(request, event) # Ensure only the owner can invite
        
        serializer = InvitationCreateSerializer(data=request.data, context={'event': event})
        if serializer.is_valid():
            invitation = Invitation.objects.create(
                event=event,
                email=serializer.validated_data['email'],
                sent_by=request.user
            )
            # email would be sent with the invite link
            invite_link = request.build_absolute_uri(f"/events/invites/accept/?token={invitation.token}")
            email = serializer.validated_data.get("email")
            event = invitation.event
            try:
                send_invite_mail(invite_link=invite_link, email_addr=email, event=event)
            except Exception as err:
                print(f"error: {err} occured!")
            return Response(
                {"message": "Invitation sent successfully.", "invite_link": invite_link},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InvitationAcceptAPIView(APIView):
    """
    Accepts an invitation using a token.
    Corresponds to User Story 3b.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(request_body=InvitationAcceptSerializer)
    def post(self, request, *args, **kwargs):
        serializer = InvitationAcceptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['token']
        invitation = get_object_or_404(Invitation, token=token, status=Invitation.Status.PENDING)

        # Ensure the logged-in user's email matches the invitation email
        if request.user.email != invitation.email:
            return Response(
                {"error": "This invitation is not for you."},
                status=status.HTTP_403_FORBIDDEN
            )
        # checks if activation is expired
        if not invitation.is_valid():
            return Response(
                {"error": "invitation link has expired, kindly request another invitation from the event owner."},
                status=status.HTTP_410_GONE
            )
        # Add user as a collaborator
        Collaborator.objects.create(
            user=request.user,
            event=invitation.event,
            role=Collaborator.Role.COLLABORATOR
        )

        # Update invitation status
        invitation.status = Invitation.Status.ACCEPTED
        invitation.save()

        return Response(
            {"message": f"Successfully joined the event: {invitation.event.name}"},
            status=status.HTTP_200_OK
        )