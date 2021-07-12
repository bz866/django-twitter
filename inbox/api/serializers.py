from rest_framework import serializers
from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Notification
        fields = (
            'timestamp',
            'actor_content_type',
            'actor_object_id',
            'action_object_content_type',
            'action_object_object_id',
            'verb',
            'target_content_type',
            'target_object_id',
            'unread',
            'description',
        )