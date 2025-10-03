from rest_framework import serializers
from notifications.models import Notification
from apps.authentication.serializers import UserSerializer

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSerializer(read_only=True)
    time_since = serializers.SerializerMethodField()
    target_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'level', 'unread', 'actor', 'verb', 'description',
            'target_content_type', 'target_object_id',
            'action_object_content_type', 'action_object_object_id',
            'timestamp', 'time_since', 'target_url', 'public'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_time_since(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.timestamp)
    
    def get_target_url(self, obj):
        if obj.target and hasattr(obj.target, 'get_absolute_url'):
            return obj.target.get_absolute_url()
        return None