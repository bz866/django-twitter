from friendships.models import Friendship
from rest_framework import serializers
from accounts.api.serializer import UserSerializerForFriendship
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError


class FriendshipFollowerSerializer(serializers.ModelSerializer):
    user = UserSerializerForFriendship(source='from_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendship
        fields = ['user', 'created_at']


class FriendshipFollowingSerializer(serializers.ModelSerializer):
    user = UserSerializerForFriendship(source='to_user')
    created_at = serializers.DateTimeField()

    class Meta:
        model = Friendship
        fields = ['user', 'created_at']


class FriendshipCreateSerializer(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ['from_user_id', 'to_user_id']

    def validate(self, attrs):
        from_user_id = attrs['from_user_id']
        to_user_id = attrs['to_user_id']
        # not support follow myself
        if from_user_id == to_user_id:
            raise ValidationError({
                'message': [
                    'from_user_id should be different from the to_user_id.'
                ],
            })

        # to_user not exists
        if not User.objects.filter(id=to_user_id).exists():
            raise ValidationError({
                'message': [
                    "to_user_id not exists."
                ],
            })
        return attrs

    def create(self, validated_data):
        from_user_id = validated_data['from_user_id']
        to_user_id = validated_data['to_user_id']
        # Friendship not exist, create new friendship
        friendship = Friendship.objects.create(from_user_id=from_user_id, to_user_id=to_user_id)
        return friendship


