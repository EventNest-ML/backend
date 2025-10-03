from django.urls import path
from . import views

urlpatterns = [
    # Budget URLs
    path('<uuid:budget_id>/', views.BudgetDetailView.as_view(), name='budget-detail'),
    path('<uuid:budget_id>/toggle/', views.BudgetToggleView.as_view(), name='budget-toggle'),
    
    # Expense URLs
    path('<uuid:budget_id>/expenses/', views.ExpenseListCreateView.as_view(), name='expense-list-create'),
    path('expenses/<uuid:expense_id>/', views.ExpenseDetailView.as_view(), name='expense-detail'),
    
    # Comment URLs
    path('expenses/<uuid:expense_id>/comments/', views.ExpenseCommentListCreateView.as_view(), name='expense-comments'),
    path('expenses/<uuid:expense_id>/typing/', views.update_typing_status, name='update-typing'),
    path('expenses/<uuid:expense_id>/typing-users/', views.get_typing_users, name='get-typing-users'),
]
