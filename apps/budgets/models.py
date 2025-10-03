# models.py
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from djmoney.models.fields import MoneyField
from apps.events.models import TimeStampedUUIDModel, Collaborator, Event


class Budget(TimeStampedUUIDModel):
    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='budget', to_field='id')
    estimated_amount = MoneyField(
        max_digits=14, 
        decimal_places=2, 
        default_currency='NGN',
        default=0
    )
    is_enabled = models.BooleanField(default=False, help_text="Budget must be enabled to allow editing")
    
    def __str__(self):
        return f'{self.event.name} Budget - {"Enabled" if self.is_enabled else "Disabled"}'
    
    
    @property
    def total_estimated_expenses(self):
        """Calculate total estimated cost of all expenses"""
        return sum(
            expense.estimated_cost if expense.estimated_cost else 0 
            for expense in self.expenses.all()
        )
    
    @property
    def total_actual_expenses(self):
        """Calculate total actual cost of all expenses"""
        return sum(
            expense.actual_cost if expense.actual_cost else 0 
            for expense in self.expenses.all()
        )
    
    @property
    def remaining_budget(self):
        """Calculate remaining budget based on actual expenses"""
        if self.estimated_amount:
            return self.estimated_amount.amount - self.total_actual_expenses
        return 0

    class Meta:
        verbose_name = "Budget"
        verbose_name_plural = "Budgets"


class Expense(TimeStampedUUIDModel):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled')
    ]

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='expenses', to_field='id')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    estimated_cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    assignee = models.ForeignKey(Collaborator, on_delete=models.CASCADE, related_name='assigned_expenses')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    due_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.name} - {self.estimated_cost or "No estimate"}'

    @property
    def currency(self):
        return self.budget.estimated_amount_currency

    @property
    def cost_difference(self):
        """Calculate the difference between estimated and actual cost"""
        if self.estimated_cost and self.actual_cost:
            if self.estimated_cost.currency == self.actual_cost.currency:
                return self.actual_cost - self.estimated_cost
        return None

    @property
    def is_over_budget(self):
        """Check if actual cost exceeds estimated cost"""
        if self.estimated_cost and self.actual_cost:
            return self.actual_cost > self.estimated_cost
        return False
    
    @property
    def can_be_edited(self):
        """Check if expense can be edited based on budget status"""
        return self.budget.is_enabled

    class Meta:
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ['-created_at']


class Comment(TimeStampedUUIDModel):
    """Generic comment model that can be used across the application"""
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=36)  # UUID field
    content_object = GenericForeignKey('content_type', 'object_id')
    
    author = models.ForeignKey(Collaborator, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    is_edited = models.BooleanField(default=False)
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.CASCADE, 
        related_name='replies',
        to_field='id'
    )
    
    def __str__(self):
        try:
            return f'Comment by {self.author} on {self.content_object}'
        except (ValueError, AttributeError):
            return f'Comment by {self.author} on {self.content_type.model} (ID: {self.object_id})'
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    def get_replies(self):
        return self.replies.all().order_by('created_at')

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['created_at']


class TypingStatus(models.Model):
    """Track who is currently typing in expense comments"""
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='typing_users')
    collaborator = models.ForeignKey(Collaborator, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['expense', 'collaborator']