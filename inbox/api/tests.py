from testing.testcases import TestCase
from rest_framework.test import APIClient
from notifications.models import Notification

COMMENT_CREATE_URL = '/api/comments/'
LIKE_CREATE_URL = '/api/likes/'


class NotificationTest(TestCase):

    def setUp(self) -> None:
        # dummy user
        self.user1 = self.create_user(username='user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(user=self.user1)
        self.user2 = self.create_user(username='user2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(user=self.user2)
        # dummy tweet
        self.tweet = self.create_tweet(user=self.user1)

    def test_comment_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        # dummy comment
        response = self.user2_client.post(
            COMMENT_CREATE_URL,
            {'tweet_id': self.tweet.id, 'content': 'default'}
        )
        self.assertEqual(response.status_code, 201)
        # dispatch notification in commenting others posts
        self.assertEqual(Notification.objects.count(), 1)
        # comment on self-owned posts doesn't dispatch notification
        self.user1_client.post(
            COMMENT_CREATE_URL,
            {'tweet_id': self.tweet.id, 'content': 'default'}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)

    def test_like_create_api_trigger_notification(self):
        self.assertEqual(Notification.objects.count(), 0)
        # like self-owned tweet doesn't not dispatch notifications
        response = self.user1_client.post(
            LIKE_CREATE_URL,
            {'content_type': 'tweet', 'object_id': self.tweet.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.count(), 0)

        # dummy comment
        comment = self.create_comment(user=self.user2, tweet=self.tweet)
        # like self-owned comment doesn't not dispatch notifications
        response = self.user2_client.post(
            LIKE_CREATE_URL,
            {'content_type': 'comment', 'object_id': comment.id}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notification when tweet liked by others
        self.user2_client.post(
            LIKE_CREATE_URL,
            {'content_type': 'tweet', 'object_id': self.tweet.id}
        )
        self.assertEqual(Notification.objects.count(), 1)

        # dispatch notifications when comment liked by others
        self.user1_client.post(
            LIKE_CREATE_URL,
            {'content_type': 'comment', 'object_id': comment.id}
        )
        self.assertEqual(Notification.objects.count(), 2)
