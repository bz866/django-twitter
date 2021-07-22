from rest_framework import serializers
from accounts.api.serializers import UserSerializerForComment
from comments.models import Comment
from tweets.models import Tweet
from rest_framework.exceptions import ValidationError
from likes.services import LikeService


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerForComment(source='cached_user')
    like_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'id',
            'tweet_id',
            'user',
            'created_at',
            'updated_at',
            'content',
            'like_count',
            'has_liked',
        )

    def get_like_count(self, obj):
        return obj.like_set.count()

    def get_has_liked(self, obj):
        return LikeService.get_has_liked(
            user=self.context['request'].user,
            obj=obj,
        )


class CommentSerializerForTweet(serializers.ModelSerializer):
    user = UserSerializerForComment(source='cached_user')
    like_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            'user',
            'created_at',
            'content',
            'like_count',
            'has_liked',
        )

    def get_like_count(self, obj):
        return obj.like_set.count()

    def get_has_liked(self, obj):
        return LikeService.get_has_liked(
            self.context['request'].user,
            obj,
        )


class CommentSerializerForCreate(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    tweet_id = serializers.IntegerField()
    content = serializers.CharField(min_length=1, max_length=140)

    class Meta:
        model = Comment
        fields = ('tweet_id', 'user_id', 'content')

    def validate(self, attrs):
        tweet_id = attrs['tweet_id']
        # check if the tweet exists
        if not Tweet.objects.filter(id=tweet_id):
            raise ValidationError({
                'message': [
                    "tweet doesn't exist."
                ],
            })
        return attrs

    def create(self, validated_data):
        comment = Comment.objects.create(
            user_id=validated_data['user_id'],
            tweet_id=validated_data['tweet_id'],
            content=validated_data['content'],
        )
        return comment


class CommentSerializerForUpdate(serializers.ModelSerializer):
    user_id = serializers.IntegerField()
    tweet_id = serializers.IntegerField()
    content = serializers.CharField(min_length=1, max_length=140)

    class Meta:
        model = Comment
        fields = ('tweet_id', 'user_id', 'content')

    def validate(self, attrs):
        tweet_id = attrs['tweet_id']
        # check if the tweet exists
        if not Tweet.objects.filter(id=tweet_id):
            raise ValidationError({
                'message': [
                    "tweet doesn't exist."
                ],
            })
        return attrs

    def update(self, instance, validated_data):
        instance.content = validated_data['content']
        instance.save()
        return instance