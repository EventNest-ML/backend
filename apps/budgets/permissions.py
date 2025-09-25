from rest_framework import permissions
from django.shortcuts import get_object_or_404
from .models import Budget, Collaborator

class IsEventCreator(permissions.BasePermission):
    def has_permission(self, request, view):
        budget_id = view.kwargs.get('budget_id')
        print("User: ", request.user, budget_id)
        if not budget_id:
            return False
        
        budget = get_object_or_404(Budget, id=budget_id)
        print("budget: ", budget)
        return budget.event.collaborators.filter(
            collaborator__user=request.user,
            collaborator__role='ADMIN'
        ).exists()