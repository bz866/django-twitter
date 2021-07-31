from newsfeeds.models import NewsFeed
from utils.cache import USER_NEWSFEED_PATTERN
from utils.redis_helper import RedisHelper
from newsfeeds.tasks import fanout_to_followers_task


class NewsFeedService():
    @classmethod
    def fanout_to_followers(cls, tweet):

        fanout_to_followers_task.delay(tweet.id)

    @classmethod
    def load_newsfeeds_through_cache(cls, user_id):
        # queryset lazy loading
        queryset = NewsFeed.objects.filter(user_id=user_id)
        name = USER_NEWSFEED_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(name, queryset)

    @classmethod
    def push_newsfeed_to_cache(cls, newsfeed):
        # queryset lazy loading
        queryset = NewsFeed.objects.filter(user_id=newsfeed.user_id)
        name = USER_NEWSFEED_PATTERN.format(user_id=newsfeed.user_id)
        return RedisHelper.push_object_to_cache(name, queryset, newsfeed)
