from django.urls import path
from .views import (TaskListCreateAPIView, TaskRetrieveUpdateDestroyAPIView,
                    AssignedTasksListAPIView, TaskStatusUpdateAPIView, TaskCommentListCreateAPIView)

urlpatterns = [
    # List all tasks for an event OR create a task (owner only)
    path( "<uuid:event_id>/", TaskListCreateAPIView.as_view(), name="task-list-create"),

    # Retrieve, update, or delete a specific task
    path("<uuid:event_id>/<int:task_id>/", TaskRetrieveUpdateDestroyAPIView.as_view(), name="task-detail" ),

    # List tasks assigned to the current user
    path( "<uuid:event_id>/assigned/", AssignedTasksListAPIView.as_view(), name="assigned-tasks"),

    # Update the status of a specific task
    path("<uuid:event_id>/<int:task_id>/status/",TaskStatusUpdateAPIView.as_view(),name="task-status-update" ),

    # List or create comments on a specific task
    path("<uuid:event_id>/<int:task_id>/comments/",TaskCommentListCreateAPIView.as_view(), name="task-comments"),
]
