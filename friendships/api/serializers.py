from accounts.api.serializers import UserSerializerForFriendship
from accounts.services import UserService
from django.contrib.auth.models import User
from friendships.models import Friendship
from friendships.services import FriendshipService
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class BaseFriendshipSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    has_followed = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ('user', 'created_at', 'has_followed',)

    def _get_following_user_id_set(self):
        # return empty set for anonymous client
        if self.context['request'].user.is_anonymous:
            return {}
        if hasattr(self, '_cached_following_user_id_set'):
            return self._cached_following_user_id_set
        user_id_set = FriendshipService.get_following_user_id_set(
            from_user_id=self.context['request'].user.id
        )
        setattr(self, '_cached_following_user_id_set', user_id_set)
        return user_id_set

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    def get_user_id(self, obj):
        raise NotImplementedError

    def get_user(self, obj):
        user = UserService.get_user_by_id(self.get_user_id(obj))
        return UserSerializerForFriendship(user).data

    def get_created_at(self, obj):
        return obj.created_at

    def get_has_followed(self, obj):
        return self.get_user_id(obj) in self._get_following_user_id_set()


class FriendshipFollowerSerializer(BaseFriendshipSerializer):
    def get_user_id(self, obj):
        return obj.from_user_id


class FriendshipFollowingSerializer(BaseFriendshipSerializer):
    def get_user_id(self, obj):
        return obj.to_user_id


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
        return FriendshipService.follow(
            from_user_id=validated_data['from_user_id'],
            to_user_id=validated_data['to_user_id'],
        )


