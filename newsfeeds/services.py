from newsfeeds.models import NewsFeed
from utils.cache import USER_NEWSFEED_PATTERN
from utils.redis_helper import RedisHelper
from newsfeeds.tasks import fanout_to_followers_main_task


class NewsFeedService():
    @classmethod
    def fanout_to_followers(cls, tweet):
        """
        Create fanout task in Celery Message Queue
        Any workers that are monitoring the message queue has chance to take the task
        In the process, worker will handle 'fanout_to_followers_main_task' ASYNCHRONOUSLY
        If the fanout takes 1000 seconds in total, the 1000 seconds won't be seen in the user posting
        .delay will end the process immediately without interrupting other user operations

        We have only created one task here. The task information is pushed into the MQ.
        The task has not really been done yet

        Note:
            The .delay() only takes arguments that can be serialized by Celery.
            Since workers are individual processes, which may be on different machines,
            there is no way for it to know what is on the Web Sever.
            We can only pass the tweet.id to it and let the worker get exact content/info
            from the DB.
            Celery has no idea how to serialize Tweet, so it only allows id as argument
        """
        fanout_to_followers_main_task.delay(tweet.id, tweet.user_id)

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
