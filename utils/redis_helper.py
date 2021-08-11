from utils.redis_client import RedisClient
from utils.redis_serializers import DjangoModelSerializer
from django.conf import settings


class RedisHelper:

    @classmethod
    def _load_objects_to_cache(cls, name, objects):
        conn = RedisClient.get_connection()
        serialized_objects = []
        # limit the cache list size
        for object in objects:
            serialized_obj = DjangoModelSerializer.serialize(object)
            serialized_objects.append(serialized_obj)

        if serialized_objects:
            conn.rpush(name, *serialized_objects)
            conn.expire(name, settings.REDIS_KEY_EXPIRE_TIME)

    @classmethod
    def load_objects(cls, name, queryset):
        queryset = queryset[: settings.REDIS_LIST_LENGTH_LIMIT]
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
        queryset = queryset[: settings.REDIS_LIST_LENGTH_LIMIT]
        conn = RedisClient.get_connection()
        # cache miss, load all tweets from db
        if not conn.exists(name):
            cls._load_objects_to_cache(name, queryset)
            return 

        serialized_object = DjangoModelSerializer.serialize(object)
        conn.lpush(name, serialized_object)
        # limit the cache list size
        conn.ltrim(name, 0, settings.REDIS_LIST_LENGTH_LIMIT-1)

    @classmethod
    def get_count_name(cls, obj, attr):
        return "{class_name}{attr}:{object_id}".format(
            class_name=obj.__class__.__name__,
            attr=attr,
            object_id=obj.id,
        )

    @classmethod
    def incr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        name = cls.get_count_name(obj, attr)
        # cache miss then get count from db
        # db counter gets increment outside the RedisHelper
        # must assure the object already has the counter attribute
        if not conn.exists(name):
            conn.set(name, getattr(obj, attr))
            conn.expire(name, settings.REDIS_KEY_EXPIRE_TIME)
            cnt = getattr(obj, attr)
            print("NOT EXIST", cls.get_count_name(obj, attr), " ::: ", cnt)
            return getattr(obj, attr)
        # counter in cache, user cache built-in function to get increment
        cnt = conn.incr(name)
        print(cls.get_count_name(obj, attr), " ::: ", cnt)
        return cnt

    @classmethod
    def decr_count(cls, obj, attr):
        conn = RedisClient.get_connection()
        name = cls.get_count_name(obj, attr)
        # cache miss then get count from db
        # db counter gets increment outside the RedisHelper
        # must assure the object already has the counter attribute
        if not conn.exists(name):
            conn.set(name, getattr(obj, attr))
            conn.expire(name, settings.REDIS_KEY_EXPIRE_TIME)
            return getattr(obj, attr)
        # counter in cache, user cache built-in function to get increment
        return conn.decr(name)

    @classmethod
    def get_count(cls, obj, attr):
        # conn = RedisClient.get_connection()
        # name = cls.get_count_name(obj, attr)
        # # cache miss, get from db
        # if not conn.exists(name):
        #     obj.refresh_from_db()
        #     conn.set(name, getattr(obj, attr))
        #     conn.expire(name, settings.REDIS_KEY_EXPIRE_TIME)
        #     return getattr(obj, attr)
        # cnt = conn.get(name)
        # return int(cnt)
        conn = RedisClient.get_connection()
        name = cls.get_count_name(obj, attr)
        count = conn.get(name)
        if count is not None:
            return int(count)
        # cache miss, get counter from db
        obj.refresh_from_db()
        count = getattr(obj, attr)
        conn.set(name, count)
        return count

