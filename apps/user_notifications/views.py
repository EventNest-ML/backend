from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .serializers import NotificationSerializer
from .pagination import NotificationPagination



class NotificationAPIView(APIView):
    """
    Single endpoint for most notification operations
    
    GET /api/notifications/
    - List notifications with filtering
    - Query params: unread_only, level, search, page, page_size
    
    POST /api/notifications/
    - Bulk operations based on 'action' field
    - Actions: mark_read, mark_unread, delete, mark_all_read, delete_all, delete_read
    
    DELETE /api/notifications/
    - Delete all notifications (shortcut for POST with action=delete_all)
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List notifications with filtering and pagination"""
        queryset = request.user.notifications.all()
        
        # Apply filters
        queryset = self._apply_filters(request, queryset)
        
        # Pagination
        paginator = NotificationPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = NotificationSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = NotificationSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Handle bulk operations based on action parameter"""
        action = request.data.get('action')
        
        if not action:
            return Response(
                {'error': 'action parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Route to appropriate bulk action
        if action == 'mark_read':
            return self._bulk_mark_read(request)
        elif action == 'mark_unread':
            return self._bulk_mark_unread(request)
        elif action == 'delete':
            return self._bulk_delete(request)
        elif action == 'mark_all_read':
            return self._mark_all_read(request)
        elif action == 'mark_all_unread':
            return self._mark_all_unread(request)
        elif action == 'delete_all':
            return self._delete_all(request)
        elif action == 'delete_read':
            return self._delete_read(request)
        else:
            return Response(
                {'error': f'Invalid action: {action}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def delete(self, request):
        """Shortcut to delete all notifications"""
        return self._delete_all(request)
    
    def _apply_filters(self, request, queryset):
        """Apply query parameter filters"""
        # Filter by unread status
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        if unread_only:
            queryset = queryset.unread()
        
        read_only = request.query_params.get('read_only', 'false').lower() == 'true'
        if read_only:
            queryset = queryset.read()
        
        # Filter by level
        level = request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # Search functionality
        search = request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) | Q(verb__icontains=search)
            )
        
        # Filter by public status
        public = request.query_params.get('public')
        if public is not None:
            queryset = queryset.filter(public=public.lower() == 'true')
        
        return queryset.order_by('-timestamp')
    
    def _bulk_mark_read(self, request):
        """Mark selected notifications as read"""
        notification_ids = request.data.get('notification_ids', [])
        
        if not notification_ids:
            return Response(
                {'error': 'notification_ids is required for bulk mark_read'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notifications = request.user.notifications.unread().filter(id__in=notification_ids)
        marked_count = notifications.count()
        
        for notification in notifications:
            notification.mark_as_read()
        
        return Response({
            'status': 'success',
            'action': 'mark_read',
            'message': f'{marked_count} notifications marked as read',
            'marked_count': marked_count,
            'unread_count': request.user.notifications.unread().count()
        })
    
    def _bulk_mark_unread(self, request):
        """Mark selected notifications as unread"""
        notification_ids = request.data.get('notification_ids', [])
        
        if not notification_ids:
            return Response(
                {'error': 'notification_ids is required for bulk mark_unread'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notifications = request.user.notifications.read().filter(id__in=notification_ids)
        marked_count = notifications.count()
        
        for notification in notifications:
            notification.mark_as_unread()
        
        return Response({
            'status': 'success',
            'action': 'mark_unread',
            'message': f'{marked_count} notifications marked as unread',
            'marked_count': marked_count,
            'unread_count': request.user.notifications.unread().count()
        })
    
    def _bulk_delete(self, request):
        """Delete selected notifications"""
        notification_ids = request.data.get('notification_ids', [])
        
        if not notification_ids:
            return Response(
                {'error': 'notification_ids is required for bulk delete'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notifications = request.user.notifications.filter(id__in=notification_ids)
        deleted_count = notifications.count()
        notifications.delete()
        
        return Response({
            'status': 'success',
            'action': 'delete',
            'message': f'{deleted_count} notifications deleted',
            'deleted_count': deleted_count,
            'total_count': request.user.notifications.count()
        })
    
    def _mark_all_read(self, request):
        """Mark all notifications as read"""
        unread_count = request.user.notifications.unread().count()
        request.user.notifications.mark_all_as_read()
        
        return Response({
            'status': 'success',
            'action': 'mark_all_read',
            'message': f'All {unread_count} notifications marked as read',
            'marked_count': unread_count,
            'unread_count': 0
        })
    
    def _mark_all_unread(self, request):
        """Mark all notifications as unread"""
        read_count = request.user.notifications.read().count()
        
        for notification in request.user.notifications.read():
            notification.mark_as_unread()
        
        return Response({
            'status': 'success',
            'action': 'mark_all_unread',
            'message': f'All {read_count} notifications marked as unread',
            'marked_count': read_count,
            'unread_count': request.user.notifications.unread().count()
        })
    
    def _delete_all(self, request):
        """Delete all notifications"""
        total_count = request.user.notifications.count()
        request.user.notifications.all().delete()
        
        return Response({
            'status': 'success',
            'action': 'delete_all',
            'message': f'All {total_count} notifications deleted',
            'deleted_count': total_count,
            'total_count': 0
        })
    
    def _delete_read(self, request):
        """Delete only read notifications"""
        read_notifications = request.user.notifications.read()
        deleted_count = read_notifications.count()
        read_notifications.delete()
        
        return Response({
            'status': 'success',
            'action': 'delete_read',
            'message': f'{deleted_count} read notifications deleted',
            'deleted_count': deleted_count,
            'total_count': request.user.notifications.count()
        })

class NotificationDetailAPIView(APIView):
    """
    Handle individual notification operations
    
    GET /api/notifications/{id}/ - Get single notification
    POST /api/notifications/{id}/ - Mark as read/unread (action param)
    DELETE /api/notifications/{id}/ - Delete single notification
    """
    permission_classes = [IsAuthenticated]
    
    def get_object(self, request, pk):
        return get_object_or_404(request.user.notifications.all(), pk=pk)
    
    def get(self, request, pk):
        """Get single notification"""
        notification = self.get_object(request, pk)
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)
    
    def post(self, request, pk):
        """Mark individual notification as read/unread based on action"""
        notification = self.get_object(request, pk)
        action = request.data.get('action', 'mark_read')
        
        if action == 'mark_read':
            if notification.unread:
                notification.mark_as_read()
                message = 'Notification marked as read'
            else:
                message = 'Notification was already read'
        elif action == 'mark_unread':
            if not notification.unread:
                notification.mark_as_unread()
                message = 'Notification marked as unread'
            else:
                message = 'Notification was already unread'
        else:
            return Response(
                {'error': f'Invalid action: {action}. Use mark_read or mark_unread'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'status': 'success',
            'action': action,
            'message': message,
            'notification_id': pk,
            'unread_count': request.user.notifications.unread().count()
        })
    
    def delete(self, request, pk):
        """Delete individual notification"""
        notification = self.get_object(request, pk)
        notification.delete()
        
        return Response({
            'status': 'success',
            'message': 'Notification deleted',
            'notification_id': pk,
            'total_count': request.user.notifications.count()
        })

class NotificationCountAPIView(APIView):
    """
    GET /api/notifications/count/
    Get notification counts - separate endpoint since it returns different data structure
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'total': user.notifications.count(),
            'unread': user.notifications.unread().count(),
            'read': user.notifications.read().count(),
            'by_level': {
                'info': user.notifications.filter(level='info').count(),
                'success': user.notifications.filter(level='success').count(),
                'warning': user.notifications.filter(level='warning').count(),
                'error': user.notifications.filter(level='error').count(),
            }
        })