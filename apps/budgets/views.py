from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .models import Budget, Expense, Comment, TypingStatus
from apps.events.models import Collaborator
from .serializers import (
    BudgetDetailSerializer, ExpenseSerializer, CommentSerializer, CommentCreateSerializer,
    ExpenseCreateSerializer, ExpenseUpdateSerializer, BudgetUpdateSerializer
)
from rest_framework.validators import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, pagination
from .permissions import IsEventCreator


class BudgetToggleView(generics.UpdateAPIView):
    """Toggle budget enabled/disabled status"""
    queryset = Budget.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsEventCreator]
    http_method_names = ['patch']
    lookup_field = 'id'
    lookup_url_kwarg = 'budget_id'

    def get_serializer_class(self):
        """Return None to indicate no request body is expected"""
        return None

    def patch(self, request, *args, **kwargs):
        budget = self.get_object()
        budget.is_enabled = not budget.is_enabled
        budget.save()
        
        return Response({
            "message": f"Budget {'enabled' if budget.is_enabled else 'disabled'}",
            "is_enabled": budget.is_enabled
        }, status=status.HTTP_200_OK)
    

class BudgetDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update a budget (only cost & currency editable)"""
    queryset = Budget.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsEventCreator]
    lookup_field = 'id'
    lookup_url_kwarg = 'budget_id'
    http_method_names = ['get', 'patch']

    def get_serializer_class(self):
        if self.request.method in ['PATCH']:
            return BudgetUpdateSerializer
        return BudgetDetailSerializer


class ExpensePagination(pagination.PageNumberPagination):
    page_size = 10  # default page size
    page_size_query_param = "page_size"  # allow client override
    max_page_size = 100


class ExpenseListCreateView(generics.ListCreateAPIView):
    """List expenses and create new ones, restricted to event creator (ADMIN)"""
    # serializer_class = ExpenseSerializer
    # permission_classes = [permissions.IsAuthenticated, IsEventCreator]
    lookup_field = 'id'
    lookup_url_kwarg = 'budget_id'

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status']   # filter only by `status`
    ordering_fields = ['created_at', 'amount']  # optional ordering
    ordering = ['-created_at']  # default ordering
    pagination_class = ExpensePagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        expense_id = self.kwargs.get('expense_id')
        context['expense_id'] = expense_id
        return context


    def get_queryset(self):
        budget_id = self.kwargs.get('budget_id')
        return Expense.objects.filter(budget_id=budget_id)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExpenseCreateSerializer
        return ExpenseSerializer

    def perform_create(self, serializer):
        budget = get_object_or_404(Budget, id=self.kwargs.get('budget_id'))

        if not budget.is_enabled:
            raise ValidationError("Cannot add expenses to a disabled budget")

        assignee = serializer.validated_data['assignee']

        if not budget.event.collaborators.filter(collaborator__id=assignee.id).exists():
            raise ValidationError("Assignee must be a collaborator of the event")

        serializer.save(budget=budget, assignee=assignee)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete expense"""
    queryset = Expense.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'expense_id'
    http_method_names = ['get', 'patch', 'delete']
    
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ExpenseUpdateSerializer
        return ExpenseSerializer
    
    def perform_update(self, serializer):
        expense = self.get_object()
        
        # Check if budget is enabled
        if not expense.can_be_edited:
            raise ValidationError("Cannot edit expenses when budget is disabled")
        
        # Check if user is event collaborator
        if not expense.budget.event.collaborators.filter(user=self.request.user).exists():
            raise PermissionError("Only event collaborators can edit expenses")
        
        serializer.save()



class ExpenseCommentListCreateView(generics.ListCreateAPIView):
    """List and create comments for an expense"""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]


    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer  # For creating comments
        return CommentSerializer  # 
    
    def get_queryset(self):
        expense_id = self.kwargs.get('expense_id')
        expense_content_type = ContentType.objects.get_for_model(Expense)
        return Comment.objects.filter(
            content_type=expense_content_type,
            object_id=expense_id,
            parent=None  # Only root comments, replies are nested
        )
    

    def perform_create(self, serializer):
        expense = get_object_or_404(Expense, id=self.kwargs.get('expense_id'))
        
        # Check if user is event collaborator
        collaborator = Collaborator.objects.filter(
                event=expense.budget.event,
                user=self.request.user
            )
        # collaborator = expense.budget.event.collaborators.filter(user=self.request.user).first()
        if not collaborator:
            raise PermissionError("Only event collaborators can comment on expenses")
        
        expense_content_type = ContentType.objects.get_for_model(Expense)
        serializer.save(
            author=collaborator.first(),
            content_type=expense_content_type,
            object_id=str(expense.id)
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_typing_status(request, expense_id):
    """Update typing status for expense comments"""
    expense = get_object_or_404(Expense, id=expense_id)
    
    collaborator = Collaborator.objects.get(
        event=expense.budget.event,
        user=request.user
    )

    if not collaborator:
        return Response(
            {"error": "Only event collaborators can participate in comments"}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    is_typing = request.data.get('is_typing', False)
    
    typing_status, created = TypingStatus.objects.get_or_create(
        expense=expense,
        collaborator=collaborator,
        defaults={'is_typing': is_typing}
    )
    
    if not created:
        typing_status.is_typing = is_typing
        typing_status.save()
    
    return Response({"status": "updated"})


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_typing_users(request, expense_id):
    """Get list of users currently typing"""
    expense = get_object_or_404(Expense, id=expense_id)
    
    # Clean up old typing statuses (older than 10 seconds)
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(seconds=10)
    TypingStatus.objects.filter(
        expense=expense,
        last_activity__lt=cutoff
    ).delete()
    
    typing_users = TypingStatus.objects.filter(
        expense=expense,
        is_typing=True
    ).values_list('collaborator__user__firstname', flat=True)
    
    return Response({"typing_users": list(typing_users)})