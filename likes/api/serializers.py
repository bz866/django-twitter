from rest_framework import serializers
from accounts.api.serializer import UserSerializerForLike
from likes.models import Like
from rest_framework.exceptions import ValidationError
from django.contrib.contenttypes.fields import ContentType
from comments.models import Comment
from tweets.models import Tweet


class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializerForLike()

    class Meta:
        model = Like
        fields = ('user', 'created_at',)

class LikeSerializerForCreate(serializers.ModelSerializer):
    content_type = serializers.ChoiceField(choices=['comment', 'tweet'])
    object_id = serializers.IntegerField()

    class Meta:
        model = Like
        fields = ('created_at', 'content_type', 'object_id')

    def _get_for_model(self, attrs):
        if attrs['content_type'] == 'tweet':
            return Tweet
        elif attrs['content_type'] == 'comment':
            return Comment
        return None

    def validate(self, attrs):
        model_class = self._get_for_model(attrs)
        if model_class is None:
            raise ValidationError({'content_type': 'Content type does not exist'})
        object_id = attrs['object_id']
        if not model_class.objects.filter(id=object_id).exists():
            raise ValidationError({'object_id': 'object_id doesn not exist'})

        return attrs

    def create(self, validated_data):
        model_class = self._get_for_model(validated_data)
        like, _ = Like.objects.get_or_create(
            user=self.context['request'].user,
            content_type=ContentType.objects.get_for_model(model_class),
            object_id=validated_data['object_id'],
        )
        return like
