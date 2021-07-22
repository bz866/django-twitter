from rest_framework.serializers import ModelSerializer
from tweets.api.serializers import TweetSerializer
from newsfeeds.models import NewsFeed


class NewsFeedSerializer(ModelSerializer):
    tweet = TweetSerializer(source='cached_tweet')

    class Meta:
        model = NewsFeed
        fields = ('id', 'created_at', 'tweet')

