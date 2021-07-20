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
        # client 1
        self.user1_client = APIClient()
        self.user1 = self.create_user(
            username='username1',
            password='defaultpw',
        )
        self.user1_client.force_authenticate(user=self.user1)
        # client 2
        self.user2_client = APIClient()
        self.user2 = self.create_user(
            username='username2',
            password='defaultpw',
        )
        self.user2_client.force_authenticate(user=self.user2)
        # client 3
        self.user3_client = APIClient()
        self.user3 = self.create_user(
            username='username3',
            password='defaultpw',
        )
        self.user3_client.force_authenticate(user=self.user3)

        # build friendships
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        Friendship.objects.create(from_user=self.user1, to_user=self.user3)
        Friendship.objects.create(from_user=self.user2, to_user=self.user1)
        Friendship.objects.create(from_user=self.user3, to_user=self.user2)

    def test_get_followers(self):
        # only allow GET method
        response = self.user1_client.post(FOLLOWERS_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 405)
        # anonymous client not allowed to access
        response = self.anonymous_client.get(FOLLOWERS_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 403)
        # get followers
        response = self.user1_client.get(FOLLOWERS_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['friendships']), 1)
        self.assertEqual(response.data['friendships'][0]['user']['username'], 'username2')
        # followers should be order by created_at in descending order
        response = self.user2_client.get(FOLLOWERS_URL.format(self.user2.id))
        self.assertEqual(len(response.data['friendships']), 2)
        self.assertEqual(response.data['friendships'][0]['user']['username'], 'username3')
        self.assertEqual(response.data['friendships'][1]['user']['username'], 'username1')

    def test_get_followings(self):
        # only allow GET method
        response = self.user1_client.post(FOLLOWINGS_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 405)
        # anonymous client not allowed to access
        response = self.anonymous_client.get(FOLLOWINGS_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 403)
        # get followings, order in descending order
        response = self.user1_client.get(FOLLOWINGS_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['friendships']), 2)
        self.assertEqual(response.data['friendships'][0]['user']['username'], 'username3')
        self.assertEqual(response.data['friendships'][1]['user']['username'], 'username2')

    def test_list_followers_and_followings(self):
        # only allow GET method
        response = self.user1_client.post(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user1.id},
        )
        self.assertEqual(response.status_code, 405)
        # anonymous client not allowed
        response = self.anonymous_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user1.id},
        )
        self.assertEqual(response.status_code, 403)
        # missing query type
        response = self.user1_client.get(
            LIST_FOLLOWERS_URL,
            {'user_id': self.user1.id},
        )
        self.assertEqual(response.status_code, 400)
        # wrong query type
        response = self.user1_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'wrongtype', 'user_id': self.user1.id},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, "Please check input. Query type need to be in ['followers', 'followings]")

        # LIST followers
        # allow other clients to check
        response = self.user1_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user2.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['friendships']), 2)
        # followers order by created_at in descending order
        self.assertEqual(response.data['friendships'][0]['user']['username'], 'username3')
        self.assertEqual(response.data['friendships'][1]['user']['username'], 'username1')

        # LIST followings
        response = self.user1_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followings', 'user_id': self.user2.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['friendships']), 1)
        self.assertEqual(response.data['friendships'][0]['user']['username'], 'username1')


    def test_follow(self):
        # only allow POST method
        response = self.user2_client.get(FOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 405)
        # anonymous client not allowed
        response = self.anonymous_client.post(FOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 403)
        # follow non-existed user
        response = self.user2_client.post(FOLLOW_URL.format(999)) # user_id 999 not exists
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['errors']['message'][0], "to_user_id not exists.")
        # not support follow myself
        response = self.user2_client.post(FOLLOW_URL.format(self.user2.id))  # follow myself
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['errors']['message'][0],
            'from_user_id should be different from the to_user_id.'
        )
        # follow
        response = self.user2_client.post(FOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['friendship']['from_user_id'], self.user2.id)
        self.assertEqual(response.data['friendship']['to_user_id'], self.user3.id)
        self.assertEqual(Friendship.objects.count(), 5)
        # re-follow
        response = self.user2_client.post(FOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['duplicated'], True)
        self.assertEqual(Friendship.objects.count(), 5)

    def test_unfollow(self):
        # only allow POST method
        response = self.user2_client.get(UNFOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 405)
        # anonymous client not allowed
        response = self.anonymous_client.post(UNFOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 403)
        # unfollow non-existed user
        response = self.user2_client.post(UNFOLLOW_URL.format(999))  # user_id 999 not exists
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Friendship not exists')
        # not support unfollow myself
        response = self.user2_client.post(UNFOLLOW_URL.format(self.user2.id))  # unfollow myself
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['message'], "You cannot unfollow yourself.")
        # unfollow
        response = self.user2_client.post(UNFOLLOW_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(int(response.data['deleted']), 1)
        self.assertEqual(Friendship.objects.count(), 3)
        # re-unfollow
        response = self.user2_client.post(UNFOLLOW_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Friendship not exists')
        self.assertEqual(Friendship.objects.count(), 3)


class FriendShipPaginationTest(TestCase):

    def setUp(self) -> None:
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')
        self.user3, self.user3_client = self.create_user_and_client(username='user3')
        # dummy friendship
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        Friendship.objects.create(from_user=self.user2, to_user=self.user1)
        Friendship.objects.create(from_user=self.user3, to_user=self.user1)
        Friendship.objects.create(from_user=self.user2, to_user=self.user3)
        #          user1
        #       /*       *\\
        #     /          \\*
        #     user3   *--  user2

    def test_friendship_pagination(self):
        # anonymous client not allowed
        response = self.anonymous_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user1.id}
        )
        self.assertEqual(response.status_code, 403)

        # pagination check - single page
        response = self.user2_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user1.id}
        )
        self.assertEqual(response.data['total_results'], 2)
        self.assertEqual(response.data['total_pages'], 1)
        self.assertEqual(response.data['page_number'], 1)
        self.assertFalse(response.data['has_next_page'])
        self.assertEqual(len(response.data['friendships']), 2)

        # multiple pages check
        for i in range(10):
            dummy_user = self.create_user(username='dummy{}'.format(i))
            Friendship.objects.create(
                from_user=self.user1,
                to_user=dummy_user,
            )
        response = self.user2_client.get(
            LIST_FOLLOWINGS_URL,
            {'type': 'followings', 'user_id': self.user1.id}
        )
        self.assertEqual(len(response.data['friendships']), 10) # 10 dummies in page 1
        self.assertEqual(response.data['total_results'], 11) # 10 dummies + user2
        self.assertEqual(response.data['total_pages'], 2)
        self.assertEqual(response.data['page_number'], 1)
        self.assertTrue(response.data['has_next_page'])

        # customized muliple page check
        response = self.user2_client.get(LIST_FOLLOWINGS_URL, {
            'type': 'followings',
            'user_id': self.user1.id,
            'size': 5,
            'page': 3,
        })
        self.assertEqual(len(response.data['friendships']), 1) # only user 2 in page 3
        self.assertEqual(response.data['total_results'], 11)  # 10 dummies + user2
        self.assertEqual(response.data['total_pages'], 3)
        self.assertEqual(response.data['page_number'], 3)
        self.assertFalse(response.data['has_next_page'])
        response = self.user2_client.get(LIST_FOLLOWINGS_URL, {
            'type': 'followings',
            'user_id': self.user1.id,
            'size': 5,
            'page': 2,
        })
        self.assertEqual(response.data['total_results'], 11)  # 10 dummies + user2
        self.assertEqual(response.data['total_pages'], 3)
        self.assertEqual(response.data['page_number'], 2)
        self.assertTrue(response.data['has_next_page'])

    def test_friendship_has_followed(self):
        # anonymous client not allowed
        response = self.anonymous_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user1.id}
        )
        self.assertEqual(response.status_code, 403)
        response = self.anonymous_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followings', 'user_id': self.user1.id}
        )
        self.assertEqual(response.status_code, 403)

        # has_followed status check
        response = self.user2_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user1.id}
        )
        response_friendships = response.data['friendships']
        self.assertEqual(len(response_friendships), 2)
        self.assertEqual(response_friendships[0]['user']['id'], self.user3.id)
        self.assertTrue(response_friendships[0]['has_followed'])
        self.assertEqual(response_friendships[1]['user']['id'], self.user2.id)
        self.assertFalse(response_friendships[1]['has_followed'])
        response = self.user3_client.get(
            LIST_FOLLOWERS_URL,
            {'type': 'followers', 'user_id': self.user2.id}
        )
        response_friendships = response.data['friendships']
        self.assertEqual(len(response_friendships), 1)
        self.assertEqual(response_friendships[0]['user']['id'], self.user1.id)
        self.assertTrue(response_friendships[0]['has_followed'])