from django.db.models import F
from utils.redis_helper import RedisHelper


def incr_like_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    if not created:
         return

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return

    # atomic operations for concurrency safe
    # django F translated SQL ensures concurrency safe in db level
    Tweet.objects.filter(id=instance.object_id)\
        .update(like_count=F('like_count') + 1)
    # extra counter in cache
    # the cached popular object should not be invalid frequently
    RedisHelper.incr_count(instance.content_object, 'like_count')


def decr_like_count(sender, instance, **kwargs):
    from tweets.models import Tweet

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return

    # atomic operations for concurrency safe
    # django F translated SQL ensures concurrency safe in db level
    Tweet.objects.filter(id=instance.object_id)\
        .update(like_count=F('like_count') - 1)
    # extra counter in cache
    # the cached popular object should not be invalid frequently
    RedisHelper.decr_count(instance.content_object, 'like_count')

