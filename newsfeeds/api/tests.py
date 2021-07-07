from testing.testcases import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from friendships.models import Friendship
from newsfeeds.services import NewsFeedService

LIST_NEWSFEED_URL = '/api/newsfeeds/'
POST_TWEET_URL = '/api/tweets/'

class NewsFeedTest(TestCase):

    def setUp(self) -> None:
        # create users
        self.user_1_client = APIClient()
        self.user_1 = User.objects.create_user(username='username1', password='defaultpw')
        self.user_1_client.force_authenticate(self.user_1)

        self.user_2_client = APIClient()
        self.user_2 = User.objects.create_user(username='username2', password='defaultpw')
        self.user_2_client.force_authenticate(self.user_2)

        self.user_3_client = APIClient()
        self.user_3 = User.objects.create_user(username='username3', password='defaultpw')
        self.user_3_client.force_authenticate(self.user_3)

        # create friendships
        Friendship.objects.create(from_user=self.user_1, to_user=self.user_2)
        Friendship.objects.create(from_user=self.user_2, to_user=self.user_1)
        Friendship.objects.create(from_user=self.user_3, to_user=self.user_1)

    def test_list(self):
        # post tweet
        for i in range(2):
            response = self.user_2_client.post(POST_TWEET_URL, {
                'content': "user2 #{} posting. This tweet should be fanout to my followers".format(
                    i)
            })
            self.assertEqual(response.status_code, 201)
        for i in range(1):
            response = self.user_1_client.post(POST_TWEET_URL, {
                'content': "user1 #{} posting. This tweet should be fanout to my followers".format(
                    i)
            })
            self.assertEqual(response.status_code, 201)

        # must login
        response = self.anonymous_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.status_code, 403)
        # only allow GET method
        response = self.user_2_client.post(LIST_NEWSFEED_URL)
        self.assertEqual(response.status_code, 405)

        # can see own tweets
        response = self.user_2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeed']), 3)
        # fanout to right followers
        response = self.user_1_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['newsfeed']), 3)
        response = self.user_3_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(len(response.data['newsfeed']), 1)

        # newsfeed order by created_at in descending order
        response = self.user_2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['user']['username'], 'username1')
        self.assertEqual(response.data['newsfeed'][1]['tweet']['user']['username'], 'username2')
        self.assertEqual(response.data['newsfeed'][2]['tweet']['user']['username'], 'username2')
        response = self.user_1_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['user']['username'], 'username1')
        self.assertEqual(response.data['newsfeed'][1]['tweet']['user']['username'], 'username2')
        self.assertEqual(response.data['newsfeed'][2]['tweet']['user']['username'], 'username2')

    def test_like_tweet_and_comment(self):
        # create tweet
        tweet1 = self.create_tweet(user=self.user_1)
        tweet2 = self.create_tweet(user=self.user_2)
        tweet3 = self.create_tweet(user=self.user_3)
        NewsFeedService().fanout_to_followers(tweet1)
        NewsFeedService().fanout_to_followers(tweet2)
        NewsFeedService().fanout_to_followers(tweet3)
        # create comment
        comment1 = self.create_comment(user=self.user_1, tweet=tweet1)
        comment2 = self.create_comment(user=self.user_3, tweet=tweet1)
        # create like
        self.create_like(user=self.user_3, object=tweet1)
        self.create_like(user=self.user_2, object=tweet1)
        self.create_like(user=self.user_2, object=comment1)
        self.create_like(user=self.user_3, object=comment1)

        # check tweet like
        response = self.user_1_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['id'], tweet2.id)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['comment_count'], 0)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['has_liked'], False)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['like_count'], 0)
        response = self.user_2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['newsfeed'][1]['tweet']['id'], tweet1.id)
        self.assertEqual(response.data['newsfeed'][1]['tweet']['comment_count'], 2)
        self.assertEqual(response.data['newsfeed'][1]['tweet']['has_liked'], True)
        self.assertEqual(response.data['newsfeed'][1]['tweet']['like_count'], 2)
        response = self.user_3_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['id'], tweet3.id)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['comment_count'], 0)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['has_liked'], False)
        self.assertEqual(response.data['newsfeed'][0]['tweet']['like_count'], 0)
        self.assertEqual(response.data['newsfeed'][1]['tweet']['id'], tweet1.id)
        self.assertEqual(response.data['newsfeed'][1]['tweet']['comment_count'], 2)
        self.assertEqual(response.data['newsfeed'][1]['tweet']['has_liked'], True)
        self.assertEqual(response.data['newsfeed'][1]['tweet']['like_count'], 2)
