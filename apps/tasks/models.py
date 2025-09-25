from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from ..events.models import  Event

# Create your models here.

User = get_user_model()
  


class Task(models.Model):
    STATUS_TODO = "TODO"
    STATUS_IN_PROGRESS = "IN_PROGRESS"
    STATUS_DONE = "DONE"
    STATUS_CHOICES = [
        ("TODO", "To Do"),
        ("IN_PROGRESS", "In Progress"),
        ("DONE", "Done"),
    ]

   
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_tasks")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="created_tasks")
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="TODO")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date',"-created_at"]
        indexes = [
            models.Index(fields=["event", "assignee", "status"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.event})"


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="task_comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on {self.task}"
