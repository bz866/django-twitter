from datetime import timedelta
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from testing.testcases import TestCase
from tweets.constants import TweetPhotoStatus
from tweets.models import Tweet
from tweets.models import TweetPhoto
from tweets.services import TweetService
from utils.cache import USER_TWEET_PATTERN
from utils.redis_client import RedisClient
from utils.time_helper import utc_now

LIST_TWEET_URL = '/api/tweets/'


class TweetTest(TestCase):

    def setUp(self):
        self.clear_cache()
        RedisClient.clear()
        self.user_1 = User.objects.create_user(username='defaultuser1', password='defaultpw')
        self.user_2 = User.objects.create_user(username='dafaultuser2', password='defaultpw')

    def test_tweet_utc_time(self):
        tweet_1 = Tweet.objects.create(
            user=self.user_1,
            content='defaultcontent',
        )
        self.assertEqual(tweet_1.hours_to_now, 0)
        tweet_1.created_at = utc_now() - timedelta(hours=10)
        self.assertEqual(tweet_1.hours_to_now, 10)


class TweetPhotoTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        RedisClient.clear()
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')
        self.tweet = self.create_tweet(user=self.user1)

    def test_tweetphoto(self):
        self.assertEqual(TweetPhoto.objects.count(), 0)
        tweetphoto1 = TweetPhoto.objects.create(
            tweet=self.tweet,
            user=self.user1,
        )
        self.assertEqual(TweetPhoto.objects.count(), 1)
        self.assertEqual(tweetphoto1.status, TweetPhotoStatus.PENDING)
        self.assertEqual(tweetphoto1.has_deleted, False)

        tweetphoto2 = TweetPhoto.objects.create(
            tweet=self.tweet,
            user=self.user2,
        )
        self.assertEqual(TweetPhoto.objects.count(), 2)
        self.assertEqual(tweetphoto2.status, TweetPhotoStatus.PENDING)
        tweetphoto2.delete()
        self.assertEqual(TweetPhoto.objects.count(), 1)

        # bulk_create
        files = [
            SimpleUploadedFile(
                name='dummy image {}.jpg'.format(i),
                content=str.encode('dummy image'),
                content_type='image/jpeg',
            )
            for i in range(5)
        ]
        photos = [
            TweetPhoto(
                user=self.user1,
                tweet=self.tweet,
                file=file,
                order = i,
            )
            for i, file in enumerate(files)
        ]
        TweetPhoto.objects.bulk_create(photos)
        self.assertEqual(TweetPhoto.objects.count(), 6)


class TweetCacheTest(TestCase):
    def setUp(self) -> None:
        self.clear_cache()
        RedisClient.clear()
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')

    def test_tweet_cache(self):
        tweet_ids = [
            self.create_tweet(user=self.user1).id
            for i in range(3)
        ]
        tweet_ids = tweet_ids[::-1]

        # cache miss
        response = self.user2_client.get(LIST_TWEET_URL, {
            'user_id': self.user1.id
        })
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(
            [response.data['results'][i]['id'] for i in range(3)],
            tweet_ids
        )

        # cache hit
        response = self.user2_client.get(LIST_TWEET_URL, {
            'user_id': self.user1.id
        })
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(
            [response.data['results'][i]['id'] for i in range(3)],
            tweet_ids
        )

        # create a new tweet, reload cache
        new_tweet = self.create_tweet(user=self.user1)
        tweet_ids.insert(0, new_tweet.id)
        response = self.user2_client.get(LIST_TWEET_URL, {
            'user_id': self.user1.id
        })
        self.assertEqual(len(response.data['results']), 4)
        self.assertEqual(
            [response.data['results'][i]['id'] for i in range(4)],
            tweet_ids
        )

    def test_create_tweet_before_get_cached_tweets(self):
        tweet1 = self.create_tweet(user=self.user1)

        RedisClient.clear()
        conn = RedisClient.get_connection()
        name = USER_TWEET_PATTERN.format(user_id=self.user1.id)
        self.assertFalse(conn.exists(name))
        tweet2 = self.create_tweet(user=self.user1)
        self.assertTrue(conn.exists(name))

        tweets = TweetService.load_tweets_through_cache(user_id=self.user1.id)
        self.assertEqual(
            [t.id for t in tweets],
            [tweet2.id, tweet1.id]
        )
