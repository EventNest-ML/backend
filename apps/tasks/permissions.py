from rest_framework import permissions
from .models import Task, TaskComment


class IsTaskOwnerOrAssigneeOrReadOnly(permissions.BasePermission):
    """
    - Event owner (task.event.owner): full control (create, edit, delete, reassign).
    - Assignee (task.assignee): can update status, add comments.
    - Collaborators: read-only access.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # Case 1: Task object
        if isinstance(obj, Task):
            # Event owner = full control
            if obj.event.owner == user:
                return True

            # Assignee = limited rights
            if obj.assignee == user:
                if request.method in permissions.SAFE_METHODS:
                    return True
                if request.method in ["PATCH", "PUT"]:
                    # Assignee can only update `status`
                    allowed_keys = {"status"}
                    if set(request.data.keys()) <= allowed_keys:
                        return True
                return False

            # Other collaborators = read-only
            return request.method in permissions.SAFE_METHODS

        # Case 2: TaskComment object
        if isinstance(obj, TaskComment):
            # Owner of event OR author of comment = can modify
            if obj.task.event.owner == user or obj.author == user:
                return True
            # Others = read-only
            return request.method in permissions.SAFE_METHODS

        return False
