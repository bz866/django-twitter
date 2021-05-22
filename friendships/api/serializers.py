from friendships.models import Friendship
from rest_framework import serializers
from accounts.api.serializer import UserSerializerForFriendship


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

