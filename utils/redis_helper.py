from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
from django.conf import settings


class RedisHelper:
    conn = RedisClient.get_connection()

    @classmethod
    def _load_tweets_to_cache(cls, name, queryset):
        serialized_tweets = []
        for object in queryset:
            serialized_obj = DjangoModelSerializer.serialize(object)
            serialized_tweets.append(serialized_obj)

        if serialized_tweets:
            cls.conn.rpush(name, *serialized_tweets)
            cls.conn.expire(name, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, name, queryset):
        if cls.conn.exists(name):
            objects = []
            serialized_tweets = cls.conn.lrange(name, 0, -1)
            for serialized_tweet in serialized_tweets:
                object = DjangoModelSerializer.deserialize(serialized_tweet)
                objects.append(object)
            return objects

        # cache miss
        cls._load_tweets_to_cache(name, queryset)
        # format output as list, Redis output is List
        return list(queryset)

    @classmethod
    def push_object_to_cache(cls, name, queryset, object):
        # cache miss, load all tweets from db
        if not cls.conn.exists(name):
            return cls._load_tweets_to_cache(name, queryset)

        serialized_object = DjangoModelSerializer.serialize(object)
        cls.conn.lpush(name, serialized_object)
