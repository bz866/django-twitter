from tweets.models import Tweet
from accounts.api.serializer import UserSerializerForTweet
from rest_framework import serializers


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet()

    class Meta:
        model = Tweet
        fields = ['id', 'user', 'created_at', 'content']

    def validate(self, attrs):
        pass

    def create(self, validated_data):
        pass
