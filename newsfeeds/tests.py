from  newsfeeds.services import NewsFeedService
from friendships.models import Friendship
from testing.testcases import TestCase
from utils.cache import USER_NEWSFEED_PATTERN
from utils.redis_client import RedisClient

LIST_NEWSFEED_URL = '/api/newsfeeds/'


class NewsFeedCacheTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        RedisClient.clear()
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')
        self.user3, self.user3_client = self.create_user_and_client(username='user3')
        # dummy friendship
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        Friendship.objects.create(from_user=self.user2, to_user=self.user1)
        Friendship.objects.create(from_user=self.user3, to_user=self.user1)
        Friendship.objects.create(from_user=self.user2, to_user=self.user3)
        #          user1
        #       /*       *\\
        #     /            \\*
        #     user3   *--  user2

    def test_newsfeed_cache(self):
        newsfeed_ids = []
        for i in range(3):
            tweet = self.create_tweet(user=self.user1)
            newsfeed = self.create_newsfeed(user=self.user2, tweet=tweet)
            newsfeed_ids.append(newsfeed.id)
        newsfeed_ids = newsfeed_ids[::-1]

        # cache miss
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual([
            response.data['results'][i]['id']
            for i in range(3)
        ], newsfeed_ids)

        # cache hit
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual([
            response.data['results'][i]['id']
            for i in range(3)
        ], newsfeed_ids)

        # create a new newsfeed, reload to cache
        tweet = self.create_tweet(user=self.user3)
        newsfeed = self.create_newsfeed(user=self.user2, tweet=tweet)
        newsfeed_ids.insert(0, newsfeed.id)
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(len(response.data['results']), 4)
        self.assertEqual([
            response.data['results'][i]['id']
            for i in range(4)
        ], newsfeed_ids)

    def test_create_newsfeed_before_get_cached_newsfeeds(self):
        feed1 = self.create_newsfeed(
            user=self.user2,
            tweet=self.create_tweet(user=self.user1)
        )

        RedisClient.clear()
        conn = RedisClient.get_connection()
        name = USER_NEWSFEED_PATTERN.format(user_id=self.user2.id)
        self.assertFalse(conn.exists(name))
        feed2 = self.create_newsfeed(
            user=self.user2,
            tweet=self.create_tweet(user=self.user3)
        )
        self.assertTrue(conn.exists(name))

        feeds = NewsFeedService.load_newsfeeds_through_cache(self.user2.id)
        self.assertEqual(
            [f.id for f in feeds],
            [feed2.id, feed1.id]
        )
