from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Task, TaskComment
from .serializers import (
    TaskSerializer,
    TaskStatusUpdateSerializer,
    TaskCommentSerializer,
)
from .permissions import IsTaskOwnerOrAssigneeOrReadOnly
from ..events.models import Event

# Create your views here.



class TaskListCreateAPIView(generics.ListCreateAPIView):
    """
    List all tasks for an event or create a new task (owner only).
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrAssigneeOrReadOnly]

    @swagger_auto_schema(
        operation_summary="List Tasks",
        operation_description="Retrieve all tasks for a given event (owner & collaborators) "
                              "or create a new task (only the event owner).",
        responses={200: TaskSerializer(many=True), 201: TaskSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Create Task",
        operation_description="Create a new task for an event. Only the event owner can perform this action.",
        request_body=TaskSerializer,
        responses={201: TaskSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        event_id = self.kwargs.get("event_id")
     
        event = get_object_or_404(Event, id=event_id)
        if not (event.owner == self.request.user or event.collaborators.filter(pk=self.request.user.pk).exists()):
            raise PermissionDenied("You are not a collaborator on this event.")
        return Task.objects.filter(event=event).select_related("assignee", "created_by")

    def perform_create(self, serializer):
        event_id = self.kwargs.get("event_id")
        event = get_object_or_404(Event, id=event_id)
        if event.owner != self.request.user:
            raise PermissionDenied("Only the event owner may create tasks.")
        serializer.save(event=event, created_by=self.request.user)


class TaskRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a task.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrAssigneeOrReadOnly]
    lookup_url_kwarg = "task_id"

    @swagger_auto_schema(
        operation_summary="Retrieve Task",
        operation_description="Retrieve a single task by ID if the user is the event owner or a collaborator.",
        responses={200: TaskSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update Task",
        operation_description="Update task details (only event owner). "
                              "Assignee can update status if PATCH request contains only 'status'.",
        request_body=TaskSerializer,
        responses={200: TaskSerializer},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially Update Task",
        operation_description="Event owner can partially update any field. "
                              "Assignee can only update 'status'.",
        request_body=TaskSerializer,
        responses={200: TaskSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Delete Task",
        operation_description="Delete a task (only event owner).",
        responses={204: "No Content"},
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_queryset(self):
        event_id = self.kwargs.get("event_id")
        event = get_object_or_404(Event, id=event_id)
        if not (event.owner == self.request.user or event.collaborators.filter(pk=self.request.user.pk).exists()):
            raise PermissionDenied("You are not a collaborator on this event.")
        return Task.objects.filter(event=event).select_related("assignee", "created_by")


class AssignedTasksListAPIView(generics.ListAPIView):
    """
    List tasks assigned to the current user within an event.
    """
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="List Assigned Tasks",
        operation_description="Retrieve all tasks assigned to the logged-in user for a given event.",
        responses={200: TaskSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        event_id = self.kwargs.get("event_id")
        event = get_object_or_404(Event, pk=event_id)
        if not (event.owner == self.request.user or event.collaborators.filter(pk=self.request.user.pk).exists()):
            raise PermissionDenied("You are not a collaborator on this event.")
        return Task.objects.filter(event=event, assignee=self.request.user)


class TaskStatusUpdateAPIView(generics.UpdateAPIView):
    """
    Update only the status of a task (assignee or owner).
    """
    serializer_class = TaskStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrAssigneeOrReadOnly]
    lookup_url_kwarg = "task_id"

    @swagger_auto_schema(
        operation_summary="Update Task Status",
        operation_description="Update only the status of a task. "
                              "Allowed for the task assignee or event owner.",
        request_body=TaskStatusUpdateSerializer,
        responses={200: TaskStatusUpdateSerializer},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_queryset(self):
        event_id = self.kwargs.get("event_id")
        event = get_object_or_404(Event, pk=event_id)
        if not (event.owner == self.request.user or event.collaborators.filter(pk=self.request.user.pk).exists()):
            raise PermissionDenied("You are not a collaborator on this event.")
        return Task.objects.filter(event=event)


class TaskCommentListCreateAPIView(generics.ListCreateAPIView):
    """
    List or create comments on a task.
    """
    serializer_class = TaskCommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsTaskOwnerOrAssigneeOrReadOnly]
    lookup_url_kwarg = "task_id"

    @swagger_auto_schema(
        operation_summary="List Task Comments",
        operation_description="Retrieve all comments for a specific task.",
        responses={200: TaskCommentSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Add Task Comment",
        operation_description="Add a comment to a task. Allowed for assignee, owner, or collaborators.",
        request_body=TaskCommentSerializer,
        responses={201: TaskCommentSerializer},
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        event_id = self.kwargs.get("event_id")
        task_id = self.kwargs.get("task_id")

        event = get_object_or_404(Event, id=event_id)
        task = get_object_or_404(Task, pk=task_id, event=event)

        if not (event.owner == self.request.user or event.collaborators.filter(pk=self.request.user.pk).exists()):
            raise PermissionDenied("You are not a collaborator on this event.")
        return TaskComment.objects.filter(task=task)

    def perform_create(self, serializer):
        event_id = self.kwargs.get("event_id")
        task_id = self.kwargs.get("task_id")

        event = get_object_or_404(Event, id=event_id)
        task = get_object_or_404(Task, pk=task_id, event=event)

        if not (event.owner == self.request.user or event.collaborators.filter(pk=self.request.user.pk).exists()):
            raise PermissionDenied("You are not a collaborator on this event.")
        serializer.save(task=task, author=self.request.user)
