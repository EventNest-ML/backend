from django.urls import path
from . import views

urlpatterns = [
    # Budgets
    path('<uuid:event_id>/budgets/', views.BudgetListCreateView.as_view(), name='budget-list-create'),

    # Expenses
    path('<uuid:event_id>/expenses/', views.ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('<int:pk>/', views.ExpenseStatusUpdateView.as_view(), name='expense-status-update'),

    path('<uuid:budget_id>/summary/', views.BudgetSummaryView.as_view(), name='budget-summary'),
]
