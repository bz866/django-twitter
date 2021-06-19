from testing.testcases import TestCase
from rest_framework.test import APIClient
from tweets.models import Tweet

CREATE_URL = '/api/comments/'


class CommentTest(TestCase):

    def setUp(self) -> None:
        # dummy user
        self.user1_client = APIClient()
        self.user1 = self.create_user(username='user1')
        self.user1_client.force_authenticate(user=self.user1)
        # dummy tweet
        self.tweet1 = Tweet.objects.create(
            user=self.user1,
            content='tweet 1 for comment test'
        )

    def test_create(self):
        # POST method only
        response = self.user1_client.get(CREATE_URL, {'tweet_id': self.tweet1.id, 'content': 'sample comment'})
        self.assertEqual(response.status_code, 405)
        # non-anonymous user
        response = self.anonymous_client.post(CREATE_URL, {'tweet_id': self.tweet1.id, 'content': 'sample comment'})
        self.assertEqual(response.status_code, 403)
        # only tweet_id
        response = self.user1_client.post(CREATE_URL, {'tweet_id': self.tweet1.id})
        self.assertEqual(response.status_code, 400)
        # only content
        response = self.user1_client.post(CREATE_URL, {'content': 'sample comment'})
        self.assertEqual(response.status_code, 400)
        # too long content
        response = self.user1_client.post(CREATE_URL, {
            'tweet_id': self.tweet1.id,
            'content': 'x'*141,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "Invalid Comment Input")
        # too short content
        response = self.user1_client.post(CREATE_URL, {
            'tweet_id': self.tweet1.id,
            'content': '', # at least 1 character
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "Invalid Comment Input")
        # no tweet exists
        response = self.user1_client.post(CREATE_URL, {'tweet_id': 9999, 'content': 'sample comment'})
        self.assertEqual(response.status_code, 400)

        # valid comment creation
        response = self.user1_client.post(CREATE_URL, {'tweet_id': self.tweet1.id, 'content': 'sample comment'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(response.data['tweet_id'], self.tweet1.id)
        self.assertEqual(response.data['content'], 'sample comment')

