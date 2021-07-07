from tweets.models import Tweet
from accounts.api.serializer import UserSerializerForTweet
from comments.api.serializers import CommentSerializerForTweet
from rest_framework import serializers
from likes.services import LikeService


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()
    comment_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comment_count',
            'like_count',
            'has_liked',
        )

    def get_like_count(self, obj):
        # call like_set using like_set @property in Tweet model
        return obj.like_set.count()

    def get_comment_count(self, obj):
        # call comment_set using the comment ForeignKey in Tweet model
        # django default backward FOO_set retrieving objects
        return obj.comment_set.count()

    def get_has_liked(self, obj):
        user = self.context['request'].user
        return LikeService.get_has_liked(user, obj)


class TweetSerializerForDetail(TweetSerializer):
    user = UserSerializerForTweet()
    comments = CommentSerializerForTweet(source='comment_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments',
            'comment_count',
            'like_count',
            'has_liked'
        )


class TweetCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)

    class Meta:
        model = Tweet
        fields = ('content',)

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        return tweet