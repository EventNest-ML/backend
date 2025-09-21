from django.db import models
from django.contrib.auth.models import User
from apps.events.models import TimeStampedUUIDModel, Collaborator, Event


class Budget(TimeStampedUUIDModel):
    CURRENCY_CHOICES = [
        ('naira(N)', 'Naira(N)'),
        ('dollars($)', 'Dollars($)')
    ]

    event = models.OneToOneField(Event, on_delete=models.CASCADE, related_name='budgets')
    estimated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=25, choices=CURRENCY_CHOICES, default='naira(N)')

    def __str__(self):
        return f'{self.event.name} has {self.estimated_amount} total amount of budget'

class Expense(TimeStampedUUIDModel):
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending')
    ]

    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='expense')
    name = models.CharField(max_length=255)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    assignee = models.ForeignKey(Collaborator, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f'{self.title} - {self.name}'
