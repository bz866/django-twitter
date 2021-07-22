from testing.testcases import TestCase
from rest_framework.test import APIClient
from likes.models import Like

CREATE_URL = '/api/likes/'
CANCEL_URL = '/api/likes/cancel/'


class LikeTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        # dummy user
        self.user1_client = APIClient()
        self.user1 = self.create_user(username='user1')
        self.user1_client.force_authenticate(self.user1)
        self.user2_client = APIClient()
        self.user2 = self.create_user(username='user2')
        self.user2_client.force_authenticate(self.user2)
        # dummy tweet
        self.tweet1 = self.create_tweet(user=self.user1)
        # dummy comment
        self.comment1 = self.create_comment(user=self.user1, tweet=self.tweet1)
        self.comment2 = self.create_comment(user=self.user2, tweet=self.tweet1)

    def test_like_tweet(self):
        data = {'content_type': 'tweet', 'object_id': self.tweet1.id}
        # POST method only
        response = self.user1_client.get(CREATE_URL, data)
        self.assertEqual(response.status_code, 405)
        # non-anonymous user
        response = self.anonymous_client.post(CREATE_URL, data)
        self.assertEqual(response.status_code, 403)
        # missing content_type
        response = self.user1_client.post(CREATE_URL, {'object_id': self.tweet1.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'missing content_type in request')
        # missing object_id
        response = self.user1_client.post(CREATE_URL, {'content_type': 'tweet'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'missing object_id in request')
        # invalid content_type
        response = self.user1_client.post(CREATE_URL, {
            'content_type': 'twitter',
            'object_id': self.tweet1.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['error'], True)
        # invalid object_id
        response = self.user1_client.post(CREATE_URL, {
            'content_type': 'tweet',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['error'], True)
        # create like
        response = self.user1_client.post(CREATE_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Like.objects.count(), 1)
        # ignore duplicated like creations
        response = self.user1_client.post(CREATE_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Like.objects.count(), 1)
        response = self.user2_client.post(CREATE_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Like.objects.count(), 2)

    def test_like_comment(self):
        data = {'content_type': 'comment', 'object_id': self.comment1.id}
        # POST method only
        response = self.user1_client.get(CREATE_URL, data)
        self.assertEqual(response.status_code, 405)
        # non-anonymous user
        response = self.anonymous_client.post(CREATE_URL, data)
        self.assertEqual(response.status_code, 403)
        # missing content_type
        response = self.user1_client.post(CREATE_URL, {'object_id': self.comment1.id})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'missing content_type in request')
        # missing object_id
        response = self.user1_client.post(CREATE_URL, {'content_type': 'comment'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'missing object_id in request')
        # invalid content_type
        response = self.user1_client.post(CREATE_URL, {
            'content_type': 'twitter',
            'object_id': self.comment1.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['error'], True)
        # invalid object_id
        response = self.user1_client.post(CREATE_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['error'], True)
        # create like
        response = self.user1_client.post(CREATE_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Like.objects.count(), 1)
        # ignore duplicated like creations
        response = self.user1_client.post(CREATE_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Like.objects.count(), 1)
        response = self.user2_client.post(CREATE_URL, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Like.objects.count(), 2)

    def test_like_cancel(self):
        data_tweet1 = {'content_type': 'tweet', 'object_id': self.tweet1.id}
        data_comment1 = {'content_type': 'comment', 'object_id': self.comment1.id}
        data_comment2 = {'content_type': 'comment', 'object_id': self.comment2.id}
        # POST method only
        response = self.user1_client.get(CANCEL_URL, data_tweet1)
        self.assertEqual(response.status_code, 405)
        # non-anonymous client
        response = self.anonymous_client.post(CANCEL_URL, data_tweet1)
        self.assertEqual(response.status_code, 403)

        # invalid content_type
        response = self.user1_client.post(CANCEL_URL, {
            'content_type': 'twitter',
            'object_id': self.comment1.id,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('content_type' in response.data['error'], True)
        # invalid object_id
        response = self.user1_client.post(CANCEL_URL, {
            'content_type': 'comment',
            'object_id': -1,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual('object_id' in response.data['error'], True)

        # create likes
        self.user1_client.post(CREATE_URL, data_tweet1)
        self.user2_client.post(CREATE_URL, data_tweet1)
        self.user2_client.post(CREATE_URL, data_comment1)
        self.assertEqual(self.tweet1.like_set.count(), 2)
        self.assertEqual(self.comment1.like_set.count(), 1)
        self.assertEqual(self.comment2.like_set.count(), 0)

        # cancel like
        response = self.user2_client.post(CANCEL_URL, data_tweet1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 1)
        self.assertEqual(self.tweet1.like_set.count(), 1)

        # duplicate cancel
        response = self.user2_client.post(CANCEL_URL, data_tweet1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(self.tweet1.like_set.count(), 1)

        # cancel non-exist like
        response = self.user2_client.post(CANCEL_URL, data_comment2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(self.comment2.like_set.count(), 0)
        response = self.user1_client.post(CANCEL_URL, data_comment1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['deleted'], 0)
        self.assertEqual(self.comment1.like_set.count(), 1)


