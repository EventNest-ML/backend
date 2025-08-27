from django.shortcuts import render
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Event
from .serializers import EventSerializer
# Create your views here.

class EventListCreateAPIView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EventSerializer

    def get_queryset(self):
        """
        b) As an event owner, you want to see all your events in one dashboard.
        """
        return Event.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        """
        a) As an event owner, you want to create a new event.
        """
        serializer.save(owner=self.request.user)

class EventDetailUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EventSerializer

    def get_queryset(self):
        # Ensure the user can only access their own events
        return Event.objects.filter(owner=self.request.user)