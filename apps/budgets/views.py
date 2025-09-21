from rest_framework import generics, permissions
from .models import Budget, Expense
from apps.events.models import Event
from .serializers import BudgetSerializer, ExpenseSerializer, ExpenseStatusUpdateSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum

# Budget Views

class BudgetListCreateView(generics.ListCreateAPIView):
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        return Budget.objects.filter(event__pkid=event_id)

    def perform_create(self, serializer):
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        if self.request.user != event.owner:
            raise PermissionDenied("Only the event owner can create a budget!!!.")
        serializer.save(event=event)

# Expense Views

class ExpenseListCreateView(generics.ListCreateAPIView):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        budget_id = Budget.objects.filter(event__id=event_id).first()
        return Expense.objects.filter(budget__id=budget_id.id)

    def perform_create(self, serializer):
        # budget_id = self.kwargs['budget_id']
        event_id = self.kwargs['event_id']
        print("Event_ID", event_id)
        budget_id = Budget.objects.filter(event__id=event_id).first()
        print("Budget_ID", budget_id)

        budget = Budget.objects.get(id=budget_id.id)
        event = budget.event

        # Only event owner can assign expenses
        if self.request.user != event.owner:
            raise PermissionDenied("Only the event owner can assign expenses.")

        serializer.save(budget=budget)

class ExpenseStatusUpdateView(generics.UpdateAPIView):
    queryset = Expense.objects.all()
    serializer_class = ExpenseStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_update(self, serializer):
        expense = self.get_object()
        if self.request.user != expense.budget.event.owner:
            raise PermissionDenied("Only the event owner can update expense status.")
        serializer.save()


class BudgetSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, budget_id):
        try:
            budget = Budget.objects.get(id=budget_id)
        except Budget.DoesNotExist:
            return Response({"error": "Budget not found"}, status=404)

        event = budget.event
        user = request.user

        # Only event owner or collaborators can view
        if user != event.owner and not event.collaborators.filter(id=user.id).exists():
            raise PermissionDenied("Not authorized to view this budget summary.")

        total_estimated = budget.expense.aggregate(
            total=Sum('estimated_cost')
        )['total'] or 0

        return Response({
            "total_estimated": total_estimated,
            "currency": budget.get_currency_display()  # returns "Naira(N)" instead of "naira(N)"
        })
