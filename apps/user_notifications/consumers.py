import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from notifications.models import Notification
from apps.user_notifications.serializers import NotificationSerializer



class NotificationConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        from django.contrib.auth.models import AnonymousUser
        print("Connecting User...")
        self.user = self.scope.get("user", AnonymousUser())
        print(self.user)
        
        await self.accept()
        
        if self.user.is_anonymous:
            await self.send(text_data=json.dumps({
                'type': 'auth_status',
                'authenticated': False,
                'message': 'Please provide valid JWT token in Authorization header'
            }))
        else:
            # User is authenticated via JWT
            self.group_name = f"notifications_{self.user.id}"
            
            # Join notification group
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            await self.send(text_data=json.dumps({
                'type': 'auth_status',
                'authenticated': True,
                'user': {
                    'id': str(self.user.id),
                    'email': self.user.email,
                    'username': getattr(self.user, 'username', None)
                },
                'message': f'Authenticated as {self.user.email}'
            }))
            
            # Send existing notifications
            await self.send_existing_notifications()

    async def disconnect(self, close_code):
        print("Close Code: ", close_code)
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        print("Text Data: ", text_data)
        data = json.loads(text_data)
        print("Received Message Data: ", data)
        message_type = data.get('type')
        
        if message_type == 'mark_as_read':
            notification_id = data.get('notification_id')
            success = await self.mark_notification_as_read(notification_id)
            
            # Send confirmation back to client
            await self.send(text_data=json.dumps({
                'type': 'mark_read_response',
                'notification_id': notification_id,
                'success': success
            }))

        elif message_type == 'get_user_notifications':
            await self.send_existing_notifications()

        elif message_type == 'new_notification_message':
            await self.new_notification_message(data)

    async def new_notification_message(self, event):
        """Send new notification to WebSocket"""
        # Serialize the notification
        serialized_notification = await self.serialize_single_notification(event['notification_id'])
        
        await self.send(text_data=json.dumps({
            'type': 'new_notification',
            'notification': serialized_notification
        }))

    async def fetch_notification_messages(self, event):
        """Send new notification to WebSocket"""
        # Serialize the notification
        
        await self.send_existing_notifications()

    @database_sync_to_async
    def get_user_notifications(self):
        """Get user's unread notifications as serialized data"""
        notifications = self.user.notifications.unread()
        serializer = NotificationSerializer(notifications, many=True)
        return serializer.data

    @database_sync_to_async
    def serialize_single_notification(self, notification_id):
        """Serialize a single notification by ID"""
        try:
            notification = Notification.objects.get(id=notification_id)
            serializer = NotificationSerializer(notification)
            return serializer.data
        except Notification.DoesNotExist:
            return None

    @database_sync_to_async
    def mark_notification_as_read(self, notification_id):
        """Mark notification as read"""
        try:
            notification = self.user.notifications.get(id=notification_id)
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False
        except Exception:
            return False

    async def send_existing_notifications(self):
        """Send existing unread notifications"""
        notifications = await self.get_user_notifications()
        
        await self.send(text_data=json.dumps({
            'type': 'existing_notifications',
            'notifications': notifications,
            'count': len(notifications)
        }))