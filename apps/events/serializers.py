from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'name', 'event_type', 'date', 'location', 'notes', 'owner']
        read_only_fields = ['owner']