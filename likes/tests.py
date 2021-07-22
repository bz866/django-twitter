from comments.models import Comment
from likes.models import Like
from testing.testcases import TestCase
from tweets.models import Tweet

NEWSFEEDS_URL = '/api/newsfeeds/'


class LikeTest(TestCase):

    def setUp(self):
        self.clear_cache()
        # dummy users
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')
        self.user3, self.user3_client = self.create_user_and_client(username='user3')
        # dummy tweets
        self.tweet1 = self.create_tweet(user=self.user1)
        self.tweet2 = self.create_tweet(user=self.user2)
        # dummy comments
        self.comment1 = self.create_comment(user=self.user1, tweet=self.tweet1)
        self.comment2 = self.create_comment(user=self.user2, tweet=self.tweet1)
        self.comment3 = self.create_comment(user=self.user1, tweet=self.tweet2)

    def test_model(self):
        # create likes for tweets
        self.create_like(self.user1, self.tweet1)
        self.create_like(self.user1, self.tweet2)
        self.assertEqual(Like.objects.count(), 2)
        # create likes for comments
        self.create_like(self.user2, self.comment1)
        self.create_like(self.user1, self.comment2)
        self.assertEqual(Like.objects.count(), 4)
        # duplicate like creation will be ignore
        self.create_like(self.user1, self.tweet1)
        self.assertEqual(Like.objects.count(), 4)

    def test_user_cache(self):
        profile1 = self.user1.profile
        profile1.nickname = 'user1_new_nickname'
        profile1.save()

        self.create_newsfeed(self.user3, self.create_tweet(self.user1))
        self.create_newsfeed(self.user3, self.create_tweet(self.user2))

        response = self.user3_client.get(NEWSFEEDS_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user2')
        self.assertEqual(results[1]['tweet']['user']['username'], 'user1')
        self.assertEqual(
            results[0]['tweet']['user']['nickname'],
            'user1_new_nickname'
        )

