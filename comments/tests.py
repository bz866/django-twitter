from testing.testcases import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from tweets.models import Tweet
from comments.models import Comment


# Create your tests here.
class CommentModelTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        self.user_1_client = APIClient()
        self.user_1 = User.objects.create_user(username='username1', password='defaultpw')
        self.user_1_client.force_authenticate(self.user_1)

        self.tweet = Tweet.objects.create(content='default content to test comment')

    def test_comment_model(self):
        data = {
            'user': self.user_1,
            'tweet': self.tweet,
            'content': 'default comment',
        }
        comment = Comment.objects.create(**data)
        self.assertEqual(comment.user.id, self.user_1.id)
        self.assertEqual(comment.tweet.id, self.tweet.id)
        self.assertEqual(comment.tweet.content, self.tweet.content)
        self.assertEqual(comment.content, 'default comment')