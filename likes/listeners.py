from django.db.models import F
from utils.listeners import invalidate_object_cache


def incr_like_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    if not created:
         return

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return

    # atomic operations for concurrecy safe
    # django F translated SQL ensures concurrency safe in db level
    tweet = instance.content_object
    Tweet.objects.filter(id=tweet.id)\
        .update(like_count=F('like_count') + 1)
    invalidate_object_cache(sender=Tweet, instance=tweet)


def decr_like_count(sender, instance, **kwargs):
    from tweets.models import Tweet

    model_class = instance.content_type.model_class()
    if model_class != Tweet:
        return

    # atomic operations for concurrecy safe
    # django F translated SQL ensures concurrency safe in db level
    tweet = instance.content_object
    Tweet.objects.filter(id=tweet.id) \
        .update(like_count=F('like_count') - 1)
    invalidate_object_cache(sender=Tweet, instance=tweet)


