from testing.testcases import TestCase
from rest_framework.test import APIClient
from notifications.models import Notification

COMMENT_CREATE_URL = '/api/comments/'
LIKE_CREATE_URL = '/api/likes/'
NOTIFICATION_LIST_URL = '/api/notifications/'


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

class NotificationApiTest(TestCase):

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
        # dummy comment
        dummy_comment_response = self.user2_client.post(COMMENT_CREATE_URL, {
            'tweet_id': self.tweet.id,
            'content': 'default content',
        })
        # dummy like
        self.user2_client.post(LIKE_CREATE_URL, {
            'content_type': 'tweet',
            'object_id': self.tweet.id,
        })
        self.user2_client.post(LIKE_CREATE_URL, {
            'content_type': 'comment',
            'object_id': dummy_comment_response.data['id']
        })

    def test_list(self):
        # GET method only
        response = self.user1_client.post(NOTIFICATION_LIST_URL)
        self.assertEqual(response.status_code, 405)
        # non-anonymous client
        response = self.anonymous_client.get(NOTIFICATION_LIST_URL)
        self.assertEqual(response.status_code, 403)

        self.assertEqual(Notification.objects.count(), 2)
        # only list notifications for a user
        # 2 notifications for user1
        response = self.user1_client.get(NOTIFICATION_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        # 0 notifications for user2
        response = self.user2_client.get(NOTIFICATION_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        # notification list with filter
        # dummy read a notification
        notification = self.user1.notifications.first()
        notification.unread = False
        notification.save()
        response = self.user1_client.get(NOTIFICATION_LIST_URL, {'unread': True})
        self.assertEqual(response.data['count'], 1)
        response = self.user1_client.get(NOTIFICATION_LIST_URL, {'unread': False})
        self.assertEqual(response.data['count'], 1)
        # 0 notifications for user2
        response = self.user2_client.get(NOTIFICATION_LIST_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_unread_count(self):
        url_unread_count = '/api/notifications/unread-count/'
        # GET method only
        response = self.user1_client.post(url_unread_count)
        self.assertEqual(response.status_code, 405)
        # non-anonymous client
        response = self.anonymous_client.get(url_unread_count)
        self.assertEqual(response.status_code, 403)

        # only show unread count for a specific user
        response = self.user1_client.get(url_unread_count)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        response = self.user2_client.get(url_unread_count)
        self.assertEqual(response.data['count'], 0)

        # dummy read a notification
        notification = self.user1.notifications.first()
        notification.unread = False
        notification.save()
        # unread count changed
        response = self.user1_client.get(url_unread_count)
        self.assertEqual(response.data['count'], 1)
        response = self.user2_client.get(url_unread_count)
        self.assertEqual(response.data['count'], 0)

    def test_mark_all_as_read(self):
        url_mark_all_as_read = '/api/notifications/mark-all-as-read/'
        # non-anonymous client
        response = self.anonymous_client.put(url_mark_all_as_read)
        self.assertEqual(response.status_code, 403)

        # only show unread count for a specific user
        response = self.user1_client.put(url_mark_all_as_read)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['updated_count'], 2)
        response = self.user2_client.put(url_mark_all_as_read)
        self.assertEqual(response.data['updated_count'], 0)
        # slient when no unread notifications
        response = self.user1_client.put(url_mark_all_as_read)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['updated_count'], 0)
        response = self.user2_client.put(url_mark_all_as_read)
        self.assertEqual(response.data['updated_count'], 0)
