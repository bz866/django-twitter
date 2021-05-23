from testing.testcases import TestCase
from rest_framework.test import APIClient
from friendships.models import Friendship

FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'
LIST_FOLLOWERS_URL = '/api/friendships/'
LIST_FOLLOWINGS_URL = '/api/friendships/'
FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'


class FriendshipTest(TestCase):

    def setUp(self):
        # anonymous client
        self.anonymous_client = APIClient()
        # client 1
        self.user_client_1 = APIClient()
        self.user_1 = self.create_user(
            username='username1',
            password='defaultpw',
        )
        self.user_client_1.force_authenticate(user=self.user_1)
        # client 2
        self.user_client_2 = APIClient()
        self.user_2 = self.create_user(
            username='username2',
            password='defaultpw',
        )
        self.user_client_2.force_authenticate(user=self.user_2)
        # client 3
        self.user_client_3 = APIClient()
        self.user_3 = self.create_user(
            username='username3',
            password='defaultpw',
        )
        self.user_client_3.force_authenticate(user=self.user_3)

        # build friendships
        Friendship.objects.create(from_user=self.user_1, to_user=self.user_2)
        Friendship.objects.create(from_user=self.user_1, to_user=self.user_3)
        Friendship.objects.create(from_user=self.user_2, to_user=self.user_1)
        Friendship.objects.create(from_user=self.user_3, to_user=self.user_2)

    def test_get_followers(self):
        # only allow GET method
        response = self.user_client_1.post(FOLLOWERS_URL.format(self.user_1.id))
        self.assertEqual(response.status_code, 405)
        # anonymous client not allowed to access
        response = self.anonymous_client.get(FOLLOWERS_URL.format(self.user_1.id))
        self.assertEqual(response.status_code, 403)
        # get followers
        response = self.user_client_1.get(FOLLOWERS_URL.format(self.user_1.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['friendship']), 1)
        self.assertEqual(response.data['friendship'][0]['user']['username'], 'username2')
        # followers should be order by created_at in descending order
        response = self.user_client_2.get(FOLLOWERS_URL.format(self.user_2.id))
        self.assertEqual(len(response.data['friendship']), 2)
        self.assertEqual(response.data['friendship'][0]['user']['username'], 'username3')
        self.assertEqual(response.data['friendship'][1]['user']['username'], 'username1')

    def test_get_followings(self):
        # only allow GET method
        response = self.user_client_1.post(FOLLOWINGS_URL.format(self.user_1.id))
        self.assertEqual(response.status_code, 405)
        # anonymous client not allowed to access
        response = self.anonymous_client.get(FOLLOWINGS_URL.format(self.user_1.id))
        self.assertEqual(response.status_code, 403)
        # get followings, order in descending order
        response = self.user_client_1.get(FOLLOWINGS_URL.format(self.user_1.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['friendship']), 2)
        self.assertEqual(response.data['friendship'][0]['user']['username'], 'username3')
        self.assertEqual(response.data['friendship'][1]['user']['username'], 'username2')

    def test_list_followers_and_followings(self):
        # only allow GET method
        response = self.user_client_1.post(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user_1.id},
        )
        self.assertEqual(response.status_code, 405)
        # anonymous client allow to access
        response = self.anonymous_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user_1.id},
        )
        self.assertEqual(response.status_code, 200)
        # missing query type
        response = self.anonymous_client.get(
            LIST_FOLLOWERS_URL,
            {'user_id': self.user_1.id},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "Please check input. Query type missed.")
        # wrong query type
        response = self.anonymous_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'wrongtype', 'user_id': self.user_1.id},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "Please check input. Query type need to be in ['followers', 'followings]")

        # LIST followers
        # allow other clients to check
        response = self.user_client_1.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user_2.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['friendship']), 2)
        # followers order by created_at in descending order
        self.assertEqual(response.data['friendship'][0]['user']['username'], 'username3')
        self.assertEqual(response.data['friendship'][1]['user']['username'], 'username1')

        # LIST followings
        response = self.user_client_1.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followings', 'user_id': self.user_2.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['friendship']), 1)
        self.assertEqual(response.data['friendship'][0]['user']['username'], 'username1')


    def test_follow(self):
        # only allow POST method
        response = self.user_client_2.get(FOLLOW_URL.format(self.user_3.id))
        self.assertEqual(response.status_code, 405)
        # not allow anonymous client
        response = self.anonymous_client.post(FOLLOW_URL.format(self.user_3.id))
        self.assertEqual(response.status_code, 403)
        # follow non-existed user
        response = self.user_client_2.post(FOLLOW_URL.format(999)) # user_id 999 not exists
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errors']['message'][0], "to_user_id not exists.")
        # not support follow myself
        response = self.user_client_2.post(FOLLOW_URL.format(self.user_2.id))  # follow myself
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['errors']['message'][0],
            'from_user_id should be different from the to_user_id.'
        )
        # follow
        response = self.user_client_2.post(FOLLOW_URL.format(self.user_3.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['friendship']['from_user_id'], self.user_2.id)
        self.assertEqual(response.data['friendship']['to_user_id'], self.user_3.id)
        self.assertEqual(Friendship.objects.count(), 5)
        # re-follow
        response = self.user_client_2.post(FOLLOW_URL.format(self.user_3.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['duplicated'], True)
        self.assertEqual(Friendship.objects.count(), 5)

    def test_unfollow(self):
        # only allow POST method
        response = self.user_client_2.get(UNFOLLOW_URL.format(self.user_3.id))
        self.assertEqual(response.status_code, 405)
        # not allow anonymous client
        response = self.anonymous_client.post(UNFOLLOW_URL.format(self.user_3.id))
        self.assertEqual(response.status_code, 403)
        # unfollow non-existed user
        response = self.user_client_2.post(UNFOLLOW_URL.format(999))  # user_id 999 not exists
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Friendship not exists')
        # not support unfollow myself
        response = self.user_client_2.post(UNFOLLOW_URL.format(self.user_2.id))  # unfollow myself
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['message'], "You cannot unfollow yourself.")
        # unfollow
        response = self.user_client_2.post(UNFOLLOW_URL.format(self.user_1.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(int(response.data['deleted']), 1)
        self.assertEqual(Friendship.objects.count(), 3)
        # re-unfollow
        response = self.user_client_2.post(UNFOLLOW_URL.format(self.user_1.id))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Friendship not exists')
        self.assertEqual(Friendship.objects.count(), 3)


