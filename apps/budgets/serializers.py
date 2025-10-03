# serializers.py
from rest_framework import serializers
from djmoney.contrib.django_rest_framework.fields import MoneyField
from .models import Budget, Expense, Comment, TypingStatus, ContentType
from apps.events.serializers import CollaboratorSerializer
from django.db.models import Sum



class BudgetSerializer(serializers.ModelSerializer):
    estimated_amount = MoneyField(max_digits=14, decimal_places=2)
    estimated_amount_currency = serializers.CharField(read_only=True)
    total_estimated_expenses = serializers.DecimalField(read_only=True, max_digits=14, decimal_places=2)
    total_actual_expenses = serializers.DecimalField(read_only=True, max_digits=14, decimal_places=2)
    remaining_budget = serializers.ReadOnlyField()
    event_name = serializers.CharField(source='event.name', read_only=True)
    
    class Meta:
        model = Budget
        fields = [
            'id', 'event', 'event_name', 'estimated_amount', 'estimated_amount_currency', 'is_enabled',
            'total_estimated_expenses', 'total_actual_expenses', 'remaining_budget',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'event', 'created_at', 'updated_at']



class BudgetUpdateSerializer(serializers.ModelSerializer):
    estimated_amount = MoneyField(max_digits=14, decimal_places=2)
    estimated_amount_currency = serializers.ChoiceField(choices=['GBP', 'USD', 'NGN'])

    class Meta:
        model = Budget
        fields = ['estimated_amount', 'estimated_amount_currency'] 

class BudgetToggleResponseSerializer(serializers.Serializer):
    """Serializer for documenting the response of budget toggle"""
    message = serializers.CharField(read_only=True)
    is_enabled = serializers.BooleanField(read_only=True)


class ExpenseSerializer(serializers.ModelSerializer):
    estimated_cost = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, allow_null=True)
    actual_cost = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, allow_null=True)
    assignee_details = CollaboratorSerializer(source='assignee', read_only=True)
    cost_difference = serializers.ReadOnlyField()
    is_over_budget = serializers.ReadOnlyField()
    can_be_edited = serializers.ReadOnlyField()
    budget_name = serializers.CharField(source='budget.event.name', read_only=True)
    comments_count = serializers.SerializerMethodField()
    currency = serializers.CharField(read_only=True)  # <-- comes from @property

    class Meta:
        model = Expense
        fields = [
            'id', 'budget', 'budget_name', 'name', 'description',
            'estimated_cost', 'actual_cost', 'currency',     # include currency
            'assignee', 'assignee_details',
            'status', 'due_date', 'cost_difference', 'is_over_budget',
            'can_be_edited', 'comments_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'budget', 'created_at', 'updated_at']

    def get_comments_count(self, obj):
        from django.contrib.contenttypes.models import ContentType
        expense_content_type = ContentType.objects.get_for_model(Expense)
        return Comment.objects.filter(
            content_type=expense_content_type,
            object_id=str(obj.id)
        ).count()



class ExpenseCreateSerializer(serializers.ModelSerializer):
    estimated_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    actual_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    
    class Meta:
        model = Expense
        fields = [
            'name', 'description', 'estimated_cost', 'actual_cost', 
            'assignee', 'status', 'due_date'
        ]
    
    def validate_assignee(self, value):
        """Ensure assignee is a collaborator of the event"""
        budget = self.context.get('budget')
        if budget and not budget.event.collaborators.filter(id=value.id).exists():
            raise serializers.ValidationError(
                "Assignee must be a collaborator of the event"
            )
        return value


class ExpenseUpdateSerializer(serializers.ModelSerializer):
    estimated_cost = MoneyField(max_digits=14, decimal_places=2, allow_null=True, required=False)
    actual_cost = MoneyField(max_digits=14, decimal_places=2, allow_null=True, required=False)
    
    class Meta:
        model = Expense
        fields = [
            'name', 'description', 'estimated_cost', 'actual_cost', 
            'assignee', 'status', 'due_date'
        ]
    
    def validate_assignee(self, value):
        """Ensure assignee is a collaborator of the event"""
        expense = self.instance
        if expense and not expense.budget.event.collaborators.filter(id=value.id).exists():
            raise serializers.ValidationError(
                "Assignee must be a collaborator of the event"
            )
        return value


class CommentReplySerializer(serializers.ModelSerializer):
    """Nested serializer for comment replies"""
    author_name = serializers.CharField(source='author.user.get_full_name', read_only=True)
    author_details = CollaboratorSerializer(source='author', read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'author_name', 'author_details',
            'is_edited', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'author', 'created_at', 'updated_at']


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.user.get_full_name', read_only=True)
    author_details = CollaboratorSerializer(source='author', read_only=True)
    replies = CommentReplySerializer(many=True, read_only=True)
    replies_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'content', 'author', 'author_name', 'author_details',
            'is_edited', 'parent', 'replies', 'replies_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'author', 'content_type', 'object_id', 'created_at', 'updated_at'
        ]
    
    def get_replies_count(self, obj):
        return obj.replies.count()
    
    def validate_parent(self, value):
        """Ensure parent comment exists and belongs to the same object"""
        if value and value.content_object != self.context.get('content_object'):
            raise serializers.ValidationError(
                "Parent comment must belong to the same object"
            )
        return value

class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content', 'parent']
    
    def validate_content(self, value):
        """Ensure content is not empty or just whitespace"""
        if not value or not value.strip():
            raise serializers.ValidationError("Content cannot be empty")
        return value.strip()
    
    def validate_parent(self, value):
        """Ensure parent comment exists for the same expense"""
        if value:
            
            view = self.context.get('view')
            expense_id = view.kwargs.get('expense_id') if view else None
            print(f"Expense ID from context: {expense_id}")
            print("Context: ", self.context)
            if not expense_id:
                raise serializers.ValidationError("Expense ID not found in context")
                
            expense_content_type = ContentType.objects.get_for_model(Expense)
            
            # Check if parent comment belongs to the same expense
            if (value.content_type != expense_content_type or 
                str(value.object_id) != str(expense_id)):
                raise serializers.ValidationError(
                    "Parent comment must belong to the same expense"
                )
                
            # Prevent deep nesting - only allow one level of replies
            if value.parent is not None:
                raise serializers.ValidationError(
                    "Cannot reply to a reply. Please reply to the original comment."
                )
                
        return value
    
    def validate(self, attrs):
        """Additional validation if needed"""
        # You can add cross-field validation here if needed
        return attrs

# class CommentCreateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Comment
#         fields = ['content', 'parent']
    
#     def validate_parent(self, value):
#         """Ensure parent comment exists for the same expense"""
#         if value:
#             expense_id = self.context.get('expense_id')
#             from django.contrib.contenttypes.models import ContentType
#             expense_content_type = ContentType.objects.get_for_model(Expense)
            
#             if (value.content_type != expense_content_type or 
#                 value.object_id != expense_id):
#                 raise serializers.ValidationError(
#                     "Parent comment must belong to the same expense"
#                 )
#         return value


class TypingStatusSerializer(serializers.ModelSerializer):
    collaborator_name = serializers.CharField(source='collaborator.user.get_full_name', read_only=True)
    
    class Meta:
        model = TypingStatus
        fields = ['collaborator', 'collaborator_name', 'is_typing', 'last_activity']
        read_only_fields = ['collaborator', 'last_activity']


# Additional serializers for detailed responses
class ExpenseDetailSerializer(ExpenseSerializer):
    """Extended expense serializer with comments"""
    recent_comments = serializers.SerializerMethodField()
    
    class Meta(ExpenseSerializer.Meta):
        fields = ExpenseSerializer.Meta.fields + ['recent_comments']
    
    def get_recent_comments(self, obj):
        from django.contrib.contenttypes.models import ContentType
        expense_content_type = ContentType.objects.get_for_model(Expense)
        recent_comments = Comment.objects.filter(
            content_type=expense_content_type,
            object_id=str(obj.id),
            parent=None
        ).order_by('-created_at')[:5]
        
        return CommentSerializer(recent_comments, many=True).data



class BudgetDetailSerializer(BudgetSerializer):
    """Extended budget serializer with expenses summary"""
    expenses_summary = serializers.SerializerMethodField()
    recent_expenses = serializers.SerializerMethodField()
    
    class Meta(BudgetSerializer.Meta):
        fields = BudgetSerializer.Meta.fields + ['expenses_summary', 'recent_expenses']
    
    def get_expenses_summary(self, obj):
        expenses = obj.expenses.all()

        def summarize(qs):
            return {
                "count": qs.count(),
                "estimated_cost": qs.aggregate(total=Sum("estimated_cost"))["total"] or 0,
                "actual_cost": qs.aggregate(total=Sum("actual_cost"))["total"] or 0,
            }

        return {
            "total": summarize(expenses),
            "paid": summarize(expenses.filter(status="paid")),
            "pending": summarize(expenses.filter(status="pending")),
            "cancelled": summarize(expenses.filter(status="cancelled")),
        }

    
    def get_recent_expenses(self, obj):
        recent_expenses = obj.expenses.all()[:5]
        return ExpenseSerializer(recent_expenses, many=True).data