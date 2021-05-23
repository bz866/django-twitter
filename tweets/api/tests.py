from testing.testcases import TestCase
from rest_framework.test import APIClient
from tweets.models import Tweet

LIST_URL = '/api/tweets/'
CREATE_URL = '/api/tweets/'


class TweetTest(TestCase):

    def setUp(self):
        self.anonymous_client = APIClient()

        self.user1_client = APIClient()
        self.user1 = self.create_user(username='username1')
        self.user1_client.force_authenticate(user=self.user1)
        self.user1_tweets = [
            self.create_tweet(self.user1, i)
            for i in range(3) # 3 tweets for user_1
        ]

        self.user2_client = APIClient()
        self.user2 = self.create_user(username='username2')
        self.user2_tweets = [
            self.create_tweet(self.user2, i)
            for i in range(2) # 2 tweets for user_2
        ]

    def test_list_tweet(self):
        # need user_id to list all tweets belong to a user
        response = self.anonymous_client.get(LIST_URL)
        self.assertEqual(response.status_code, 400)

        # users have right number of tweets listed
        response = self.user1_client.get(LIST_URL, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweet']), 3)
        self.assertEqual(response.data['tweet'][0]['user']['username'], 'username1')
        response = self.user2_client.get(LIST_URL, {'user_id': self.user2.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tweet']), 2)
        self.assertEqual(response.data['tweet'][0]['user']['username'], 'username2')

        # tweets should be listed order by created_at in descending order
        response = self.user1_client.get(LIST_URL, {'user_id': self.user1.id})
        self.assertEqual(response.data['tweet'][0]['id'], self.user1_tweets[2].id)
        self.assertEqual(response.data['tweet'][1]['id'], self.user1_tweets[1].id)

    def test_create_tweet(self):
        # anonymous user can not create tweet
        response = self.anonymous_client.post(CREATE_URL)
        self.assertEqual(response.status_code, 403)

        # too short content
        response = self.user1_client.post(CREATE_URL, {
            'content': 'x'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "Please check the input")
        # too long content
        response = self.user1_client.post(CREATE_URL, {
            'content': '0' * 141
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "Please check the input")

        # create a tweet by user1
        response = self.user1_client.post(CREATE_URL, {
            'content': '0' * 140
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tweet']['content'], '0'*140)
        self.assertEqual(Tweet.objects.count(), 6)
        self.assertEqual(response.data['tweet']['user']['username'], 'username1')

        # create a tweet by user2
        self.user2_client.login(username='username2', password='defaultpassword')
        response = self.user2_client.post(CREATE_URL, {
            'user': self.user2,
            'content': 'default content',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tweet']['content'], "default content")
        self.assertEqual(Tweet.objects.count(), 7)
        self.assertEqual(response.data['tweet']['user']['username'], 'username2')



