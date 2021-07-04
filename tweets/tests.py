from datetime import timedelta

from django.test import TestCase
from tweets.models import Tweet
from django.contrib.auth.models import User
from utils.time_helper import utc_now


# Create your tests here.
class TweetTest(TestCase):

    def setUp(self):
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


