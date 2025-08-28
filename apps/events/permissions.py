# events/permissions.py

from rest_framework import permissions

class IsEventOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an event to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Write permissions are only allowed to the owner of the event.
        return obj.owner == request.user