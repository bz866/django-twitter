from rest_framework import serializers
from accounts.api.serializer import UserSerializerForComment
from comments.models import Comment
from tweets.models import Tweet
from rest_framework.exceptions import ValidationError


class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializerForComment()

    class Meta:
        model = Comment
        fields = ('id', 'tweet_id', 'user', 'created_at', 'content')


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
        fields = ('tweet_id', 'user_id', 'content',)

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