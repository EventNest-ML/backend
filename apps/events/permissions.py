# events/permissions.py

from rest_framework import permissions



class IsEventOwnerOrCollaboratorReadOnly(permissions.BasePermission):
    """
    Custom permission:
    - Owners can fully edit/delete the event.
    - Contributors can only view (safe methods).
    """

    def has_object_permission(self, request, view, obj):
        # SAFE_METHODS = GET, HEAD, OPTIONS
        if request.method in permissions.SAFE_METHODS:
            # Allow contributors and owner to view
            print("*************: ", obj)
            return (
                request.user == obj.owner
                or request.user in obj.collaborators.all()
            )

        # For write permissions, only the owner can edit
        return obj.owner == request.user
