from rest_framework import serializers
from .models import Budget, Expense

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = [
            'id', 
            # 'budget', 
            'name', 
            'estimated_cost',
            'actual_cost', 
            'assignee', 
            'status', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ExpenseStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['status']

class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = [
            'id',
            # 'event', 
            'estimated_amount', 
            'currency', 
            'created_at', 
            'updated_at'
            ]
        read_only_fields = [
            'id', 
            'created_at', 
            'updated_at'
            ]
