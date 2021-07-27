from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
from django.conf import settings


class RedisHelper:

    @classmethod
    def _load_objects_to_cache(cls, name, objects):
        conn = RedisClient.get_connection()
        serialized_objects = []
        # limit the cache list size
        for object in objects[:settings.REDIS_LIST_LENGTH_LIMIT]:
            serialized_obj = DjangoModelSerializer.serialize(object)
            serialized_objects.append(serialized_obj)

        if serialized_objects:
            conn.rpush(name, *serialized_objects)
            conn.expire(name, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, name, queryset):
        conn = RedisClient.get_connection()

        if conn.exists(name):
            objects = []
            serialized_tweets = conn.lrange(name, 0, -1)
            for serialized_tweet in serialized_tweets:
                object = DjangoModelSerializer.deserialize(serialized_tweet)
                objects.append(object)
            return objects

        # cache miss
        cls._load_objects_to_cache(name, queryset)
        # format output as list, Redis output is List
        return list(queryset)

    @classmethod
    def push_object_to_cache(cls, name, queryset, object):
        conn = RedisClient.get_connection()
        # cache miss, load all tweets from db
        if not conn.exists(name):
            cls._load_objects_to_cache(name, queryset)
            return 

        serialized_object = DjangoModelSerializer.serialize(object)
        conn.lpush(name, serialized_object)
        # limit the cache list size
        conn.ltrim(name, 0, settings.REDIS_LIST_LENGTH_LIMIT-1)
