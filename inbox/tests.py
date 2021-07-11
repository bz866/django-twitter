from testing.testcases import TestCase
from inbox.services import NotificationService
from notifications.models import Notification
from django.contrib.contenttypes.fields import ContentType


class NotificationTest(TestCase):

    def setUp(self) -> None:
        # dummy users
        self.user1 = self.create_user(username='user1')
        self.user2 = self.create_user(username='user2')
        # dummy tweet
        self.tweet = self.create_tweet(user=self.user1)

    def test_send_comment_notification(self):
        # dispatch notifications if comment on others tweets
        comment1 = self.create_comment(user=self.user2, tweet=self.tweet)
        NotificationService.send_comment_notification(comment1)
        self.assertEqual(Notification.objects.count(), 1)

        # do not dispatch notifications if comment self-owned tweet
        comment2 = self.create_comment(user=self.user1, tweet=self.tweet)
        NotificationService.send_comment_notification(comment2)
        self.assertEqual(Notification.objects.count(), 1)

    def test_send_like_notification(self):
        # do not dispatch notifications if like self-owned tweet
        like1 = self.create_like(user=self.user1, object=self.tweet)
        NotificationService.send_like_notification(like1)
        self.assertEqual(Notification.objects.count(), 0)

        # dispatch notifications if like on others tweets
        like2 = self.create_like(user=self.user2, object=self.tweet)
        NotificationService.send_like_notification(like2)
        self.assertEqual(Notification.objects.count(), 1)

        comment = self.create_comment(user=self.user2, tweet=self.tweet)
        # do not dispatch notifications if like self-owned comment
        like3 = self.create_like(user=self.user2, object=comment)
        NotificationService.send_like_notification(like3)
        self.assertEqual(Notification.objects.count(), 1)

        # dispatch notifications if like others comments
        like4 = self.create_like(user=self.user1, object=comment)
        NotificationService.send_like_notification(like4)
        self.assertEqual(Notification.objects.count(), 2)