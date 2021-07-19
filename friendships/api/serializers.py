from accounts.api.serializers import UserSerializerForFriendship
from django.contrib.auth.models import User
from friendships.models import Friendship
from friendships.services import FriendshipService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class FriendshipFollowerSerializer(serializers.ModelSerializer):
    user = UserSerializerForFriendship(source='from_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed',)

    def get_has_followed(self, obj):
        from_user = self.context['request'].user
        to_user = obj.from_user
        # TODO optimize the N+1 query
        return FriendshipService.has_followed(from_user, to_user)


class FriendshipFollowingSerializer(serializers.ModelSerializer):
    user = UserSerializerForFriendship(source='to_user')
    created_at = serializers.DateTimeField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed',)

    def get_has_followed(self, obj):
        from_user = self.context['request'].user
        to_user = obj.to_user
        # TODO optimize the N+1 query
        return FriendshipService.has_followed(from_user, to_user)


class FriendshipCreateSerializer(serializers.ModelSerializer):
    from_user_id = serializers.IntegerField()
    to_user_id = serializers.IntegerField()

    class Meta:
        model = Friendship
        fields = ('from_user_id', 'to_user_id')

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
        # Friendship not exist, create new friendship
        return Friendship.objects.create(
            from_user_id=validated_data['from_user_id'],
            to_user_id=validated_data['to_user_id'],
        )


