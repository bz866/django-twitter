from celery import shared_task
from newsfeeds.constants import FANOUT_BATCH_SIZE
from newsfeeds.models import NewsFeed
from utils.time_constants import ONE_HOUR


@shared_task(routing_key='newsfeeds', time_limit=ONE_HOUR)
def fanout_to_followers_batch_task(tweet_id, follower_ids):
    from newsfeeds.services import NewsFeedService

    # create newsfeed for all followers
    newsfeeds = [
        NewsFeed(user_id=follower_id, tweet_id=tweet_id)
        for follower_id in follower_ids
    ]
    # create objects by batch, more efficiency
    NewsFeed.objects.bulk_create(newsfeeds)

    # bulk_create() doesn't trigger post_save signal
    # trigger the post_save manually in iteration
    for newsfeed in newsfeeds:
        NewsFeedService.push_newsfeed_to_cache(newsfeed)

    return "{} newsfeeds have been created".format(len(newsfeeds))


@shared_task(routing_key='default', time_limit=ONE_HOUR)
def fanout_to_followers_main_task(tweet_id, tweet_user_id):
    from friendships.services import FriendshipService
    # create the newsfeed for the poster firstly
    # ensure the poster get response asap
    NewsFeed.objects.create(user_id=tweet_user_id, tweet_id=tweet_id)

    # fanout to followers in asychronous tasks
    follower_ids = FriendshipService.get_follower_ids(tweet_user_id)
    index = 0
    # batchify all asychronous tasks to reduce the size of a single task
    # ensure robust in asychronous tasks and parallelly processing batches
    while index < len(follower_ids):
        batch_ids = follower_ids[index : index+FANOUT_BATCH_SIZE]
        fanout_to_followers_batch_task(tweet_id, batch_ids)
        index += FANOUT_BATCH_SIZE

    if len(follower_ids) % FANOUT_BATCH_SIZE == 0:
        num_batches = len(follower_ids) // FANOUT_BATCH_SIZE
    else:
        num_batches = len(follower_ids) // FANOUT_BATCH_SIZE + 1

    return "{} newsfeeds are going to be fanout, " \
           "{} batches created, " \
           "batch size {}".format(
        len(follower_ids),
        num_batches,
        FANOUT_BATCH_SIZE,
    )
