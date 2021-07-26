from tweets.models import TweetPhoto
from tweets.models import Tweet
from utils.cache import USER_TWEET_PATTERN
from utils.redis_helper import RedisHelper


class TweetService:
    @classmethod
    def create_photos_from_files(cls, user, tweet, files):
        photos = []
        for index, file in enumerate(files):
            photo = TweetPhoto(
                user=user,
                tweet=tweet,
                file=file,
                order=index,
            )
            photos.append(photo)
        TweetPhoto.objects.bulk_create(photos)

    @classmethod
    def load_tweets_through_cache(cls, user_id):
        # Django query is lazy loading
        # it is triggered by iterations inside the load_object()
        queryset = Tweet.objects.filter(user_id=user_id).order_by('-created_at')
        name = USER_TWEET_PATTERN.format(user_id=user_id)
        return RedisHelper.load_objects(name, queryset)

    @classmethod
    def push_tweet_to_cache(cls, tweet):
        queryset = Tweet.objects.filter(
            user_id=tweet.user_id
        ).order_by('-created_at')
        name = USER_TWEET_PATTERN.format(user_id=tweet.user_id)
        return RedisHelper.push_tweet_to_cache(name, queryset, tweet)
