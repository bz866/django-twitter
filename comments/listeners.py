from django.db.models import F
from utils.listeners import invalidate_object_cache


def incr_comment_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    if not created:
        return

    # atomic operations for concurrecy safe
    # django F translated SQL ensures concurrency safe in db level
    Tweet.objects.filter(id=instance.tweet_id)\
        .update(comment_count=F('comment_count') + 1)
    invalidate_object_cache(sender=Tweet, instance=instance.tweet)


def decr_comment_count(sender, instance, **kwargs):
    from tweets.models import Tweet

    # atomic operations for concurrecy safe
    # django F translated SQL ensures concurrency safe in db level
    Tweet.objects.filter(id=instance.tweet_id) \
        .update(comment_count=F('comment_count') - 1)
    invalidate_object_cache(sender=Tweet, instance=instance.tweet)

