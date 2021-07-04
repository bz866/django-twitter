from tweets.models import Tweet
from accounts.api.serializer import UserSerializerForTweet
from comments.api.serializers import CommentSerializerForTweet
from rest_framework import serializers


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()

    class Meta:
        model = Tweet
        fields = ['id', 'user', 'created_at', 'content']


class TweetSerializerWithComments(serializers.ModelSerializer):
    user = UserSerializerForTweet()
    comments = CommentSerializerForTweet(source='comment_set', many=True)

    class Meta:
        model = Tweet
        fields = ['id', 'user', 'created_at', 'content', 'comments']


class TweetCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)

    class Meta:
        model = Tweet
        fields = ['content',]

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        return tweet