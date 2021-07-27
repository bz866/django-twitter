from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed
from utils.cache import USER_NEWSFEED_PATTERN
from utils.redis_helper import RedisHelper


class NewsFeedService():
    @classmethod
    def fanout_to_followers(cls, tweet):
        # get all followers of the poster
        followers = FriendshipService().get_followers(tweet.user)
        # create newsfeed for all followers
        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)
            for follower in followers
        ]
        # the poster can see own posted tweet
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        # create objects by batch, more efficiency
        NewsFeed.objects.bulk_create(newsfeeds)

        # bulk_create() doesn't trigger post_save signal
        # trigger the post_save manually in iteration
        for newsfeed in newsfeeds:
            cls.push_newsfeed_to_cache(newsfeed)

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
