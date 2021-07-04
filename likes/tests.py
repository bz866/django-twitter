from testing.testcases import TestCase
from comments.models import Comment
from tweets.models import Tweet
from likes.models import Like


class LikeTest(TestCase):

    def setUp(self):
        # dummy users
        self.user1 = self.create_user(username='user1')
        self.user2 = self.create_user(username='user2')
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
