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


class NotificationSerializerForUpdate(serializers.ModelSerializer):
    unread = serializers.BooleanField()

    class Meta:
        model = Notification
        fields = ('unread',)

    def update(self, instance, validated_data):
        """
        change the unread status only of a notification
        """
        instance.unread = validated_data['unread']
        instance.save()
        return instance