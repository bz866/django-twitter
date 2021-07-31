from utils.redis_helper import RedisHelper


def incr_comment_count(sender, instance, created, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    if not created:
        return

    # atomic operations for concurrency safe
    # django F translated SQL ensures concurrency safe in db level
    Tweet.objects.filter(id=instance.tweet_id)\
        .update(comment_count=F('comment_count') + 1)
    # extra counter in cache
    # the cached popular object should not be invalid frequently
    RedisHelper.incr_count(instance.tweet, 'comment_count')
    print("COMMENT INCR + 1")


def decr_comment_count(sender, instance, **kwargs):
    from tweets.models import Tweet
    from django.db.models import F

    # atomic operations for concurrency safe
    # django F translated SQL ensures concurrency safe in db level
    Tweet.objects.filter(id=instance.tweet_id) \
        .update(comment_count=F('comment_count') - 1)
    # extra counter in cache
    # the cached popular object should not be invalid frequently
    RedisHelper.decr_count(instance.tweet, 'comment_count')
