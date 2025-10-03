# events/views.py

from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Event, Invitation, Collaborator
from .serializers import (
    EventListSerializer,
    EventDetailSerializer,
    InvitationCreateSerializer,
    InvitationAcceptSerializer,
    CollaboratorSerializer
)
from .permissions import IsEventOwnerOrCollaboratorReadOnly, IsEventOwner

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

        # dashboard counts
        queryset = events.distinct()
        counts = {
            "total": queryset.count(),
            "ongoing": queryset.filter(status="ongoing").count(),
            "completed": queryset.filter(status="completed").count(),
            "archived": queryset.filter(status="archived").count(),
        }

        return Response({'events':serializer.data, 'counts':counts},
                         status=status.HTTP_200_OK)
    
    @swagger_auto_schema(request_body=EventDetailSerializer)
    def post(self, request, *args, **kwargs):
        # Create a new event
        serializer = EventDetailSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            event = serializer.save()
            print("EventID: ", event.id)
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

    @swagger_auto_schema(
            operation_summary="Creates and sends an invitation for an event",
            request_body=InvitationCreateSerializer)
    def post(self, request, id, *args, **kwargs):
        event = get_object_or_404(Event, id=id)
        self.check_object_permissions(request, event) # Ensure only the owner can invite
        
        serializer = InvitationCreateSerializer(data=request.data, context={'event': event, "request":request})
        if serializer.is_valid():
            invitation = Invitation.objects.create(
                event=event,
                email=serializer.validated_data['email'],
                sent_by=request.user
            )
            email = serializer.validated_data.get("email")
            event = invitation.event
            return Response(
                {"message": f"Invitation sent successfully to {email}."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InvitationRetrieveAPIView(APIView):
    """
    Validates invitation token.
    Corresponds to User Story 3b.
    Retrieves invitation details for display before user accepts/declines.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly] #I removed the authentication so that the invitee can the details without any authorization
    @swagger_auto_schema(
        operation_summary="Displays event's details before  accepting/declining an Invitation",
        manual_parameters=[
            openapi.Parameter(
                'token',
                openapi.IN_QUERY,
                description="Invitation token (UUID)",
                type=openapi.TYPE_STRING,
                required=True
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        token = request.query_params.get('token')
        
        print("*********************: ", token)
        invitation = get_object_or_404(Invitation, token=token)

        if not invitation.is_valid():
            return Response(
                {"error": "This invitation link has expired."},
                status=status.HTTP_410_GONE
            )

        return Response({
            "event": {
                "id": invitation.event.id,
                "name": invitation.event.name,
                "notes": invitation.event.notes,
                "owner": invitation.event.owner.firstname,
            },
            "email": invitation.email,
            "status": invitation.status,
        }, status=status.HTTP_200_OK)



    
class InvitationRespondAPIView(APIView):
    """
    Allows collaborators to Accept/Decline the invitation using a token.
    Corresponds to User Story 3b.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
            operation_summary="Accept/Decline the invitation",
            request_body=InvitationAcceptSerializer)
    def post(self, request, *args, **kwargs):
        serializer = InvitationAcceptSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = serializer.validated_data['token']
        action = serializer.validated_data['action']
        invitation = get_object_or_404(
            Invitation, token=token, status=Invitation.Status.PENDING
        )

        # Ensure the logged-in user's email matches
        if request.user.email != invitation.email:
            return Response(
                {"error": "This invitation is linked to another email address."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Check expiration
        if not invitation.is_valid():
            return Response(
                {"error": "This invitation link has expired."},
                status=status.HTTP_410_GONE
            )

        if action == "accept":
  
            # Add user as collaborator (avoid duplicates)
            Collaborator.objects.get_or_create(
                user=request.user,
                event=invitation.event,
                defaults={"role": Collaborator.Role.COLLABORATOR}
            )
            invitation.status = Invitation.Status.ACCEPTED
            invitation.save()
            return Response(
                {"message": f"Successfully joined {invitation.event.name}."},
                status=status.HTTP_200_OK
            )

        elif action == "decline":
            invitation.status = Invitation.Status.DECLINED
            invitation.save()
            return Response(
                {"message": f"You declined the invitation to {invitation.event.name}."},
                status=status.HTTP_200_OK
            )

#Views for Managing Contributors
class CollaboratorListAPIView(generics.ListAPIView):
    """
    List all contributors for a given event.
    """
    serializer_class = CollaboratorSerializer
    permission_classes = [permissions.IsAuthenticated,IsEventOwner]

    def get_queryset(self):
        event_id = self.kwargs["event_id"]
        return Collaborator.objects.filter(event__id=event_id)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        event_id = self.kwargs["event_id"]
        invitations = Invitation.objects.filter(event__id = event_id).distinct()
      
        counts = {"total_members": queryset.count(),
                  "active_members": queryset.count(),
                  "pending_members": invitations.filter(status="PENDING").count(),
                  }
        return Response({
            "collaborators": serializer.data,
            "counts": counts
        })
    

class CollaboratorDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a contributor for a given event.
    Only event owners can update or delete contributors.
    """

    serializer_class = CollaboratorSerializer
    permission_classes = [permissions.IsAuthenticated, IsEventOwner]

    def get_queryset(self):
        """
        Ensure we're only looking at collaborators for this event.
        """
        event_id = self.kwargs.get("event_id")
        return Collaborator.objects.filter(event__id=event_id)

    def delete(self, request, *args, **kwargs):
        collaborator = self.get_object()

        # Prevent owner from removing themselves
        if collaborator.user == request.user:
            return Response(
                {"error": "You cannot remove yourself as a contributor."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        collaborator.delete()
        return Response(
            {"message": f"{collaborator.user.email} has been removed from the event."},
            status=status.HTTP_204_NO_CONTENT,
        )
