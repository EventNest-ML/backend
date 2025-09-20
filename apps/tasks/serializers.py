from rest_framework import serializers
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Task, TaskComment
from ..events.models import Event   

User = get_user_model()


class TaskSerializer(serializers.ModelSerializer):
    """
    Full serializer for creating and updating tasks.
    - Event owner: can create, edit, reassign, delete tasks.
    - Assignee: can update status (handled separately).
    """
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all()
    )
    status = serializers.ChoiceField(
        choices=Task.STATUS_CHOICES,
        read_only=False,
        default=Task.STATUS_TODO,
    )
    event_name = serializers.CharField(source="event.name", read_only=True)

    class Meta:
        model = Task
        fields = ["id","event_name","title","description", "assignee",  "created_by", "due_date", "status", "created_at", "updated_at" ]
        read_only_fields = ("created_at", "updated_at", "created_by")
    


    def validate_assignee(self, value):
        """
        Ensure the assignee is a collaborator (or the owner).
        """
        event_id =  self.context["view"].kwargs.get("event_id")

        if not event_id:
            return value

        try:
            event = Event.objects.get(pk=event_id)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event does not exist.")

        if hasattr(event, "collaborators"):
            if (
                not event.collaborators.filter(pk=value.pk).exists()
                and event.owner != value
            ):
                raise serializers.ValidationError(
                    "Assignee must be a collaborator of the event."
                )
        return value

    def create(self, validated_data):
        """
        Set created_by automatically.
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)
        validated_data["created_by"] = user

        with transaction.atomic():
            task = super().create(validated_data)
            # 🔔 TODO: plug notification (assignee)
            return task

    def update(self, instance, validated_data):
        """
        Allow owner to update fields (including reassign).
        """
        with transaction.atomic():
            task = super().update(instance, validated_data)
            # 🔔 TODO: plug notification (if reassigned)
            return task


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for updating only the status field.
    Used by assignees or owners.
    """
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES)

    class Meta:
        model = Task
        fields = ["status"]

    def validate_status(self, value):
        """
        Optional: enforce transition rules (e.g., prevent DONE → TODO).
        Currently accepts all transitions.
        """
        return value

    def update(self, instance, validated_data):
        previous_status = instance.status
        instance.status = validated_data["status"]
        instance.save(update_fields=["status", "updated_at"])
        # 🔔 TODO: plug notification (status change)
        return instance


class TaskCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    """
    author = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TaskComment
        fields = ["id", "task", "author", "content", "created_at"]
        read_only_fields = ("id", "author", "created_at")

    def create(self, validated_data):
        request = self.context.get("request")
        validated_data["author"] = request.user
        comment = super().create(validated_data)
        # 🔔 TODO: plug notification (new comment)
        return comment
