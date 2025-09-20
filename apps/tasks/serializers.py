# apps/events/serializers.py
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from .models import Task, TaskComment
from ..events.models import Event


class TaskSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    assignee = serializers.PrimaryKeyRelatedField(queryset=settings.AUTH_USER_MODEL.objects.all())
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES, read_only=False, default=Task.STATUS_TODO)

    class Meta:
        model = Task
        fields = [
            "id",
            "event",
            "title",
            "description",
            "assignee",
            "created_by",
            "due_date",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("created_at", "updated_at", "created_by")
        extra_kwargs = {"event": {"write_only": True}}

    def validate_event(self, value):
        # ensure event exists and user has permission to add tasks (owner)
        request = self.context.get("request")
        if not request:
            return value
        user = request.user
        # Only owners allowed to create tasks (enforced at view/permission level too)
        if hasattr(value, "owner"):
            if value.owner != user:
                raise serializers.ValidationError("Only the event owner can create tasks for this event.")
        return value

    def validate_assignee(self, value):
        """
        Ensure assignee is a collaborator on the event.
        We expect `event` to be in initial_data (write_only). If not present, we cannot validate here.
        """
        event_id = self.initial_data.get("event")
        if not event_id:
            # If updating and event isn't changing, skip here.
            return value

        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event does not exist.")

        # --- ADAPT THIS BLOCK to your project's collaborator relation ---
        # Option A: Event has a ManyToManyField to user named 'collaborators'
        if hasattr(event, "collaborators"):
            if not event.collaborators.filter(pk=value.pk).exists() and event.owner != value:
                raise serializers.ValidationError("Assignee must be a collaborator of the event.")

        return value

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        validated_data["created_by"] = user
        # event is expected to be present
        with transaction.atomic():
            task = super().create(validated_data)
            # TODO: trigger notification to assignee (task assigned)
            # notify_task_assigned(task)
            return task

    def update(self, instance, validated_data):
        # Allow owner to update fields (including reassign)
        with transaction.atomic():
            task = super().update(instance, validated_data)
            # TODO: if assignee changed -> notify new assignee and previous assignee
            return task


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)

    class Meta:
        model = Task
        fields = ["status"]

    def validate_status(self, value):
        # TODO: Optionally enforce status transitions (e.g., cannot go from DONE back to TODO) — omitted for simplicity
        return value

    def update(self, instance, validated_data):
        previous_status = instance.status
        instance.status = validated_data["status"]
        instance.save(update_fields=["status", "updated_at"])
        # TODO: notify owner that assignee updated status
        return instance


class TaskCommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TaskComment
        fields = ["id", "task", "author", "content", "created_at"]
        read_only_fields = ("id", "author", "created_at")

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["author"] = request.user
        comment = super().create(validated_data)
        # TODO: notify interested parties about the new comment (e.g., task assignee & event owner)
        return comment
