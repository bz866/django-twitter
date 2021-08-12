from django.conf import settings
from django.core.cache import caches
from friendships.services import FriendshipService
from gatekeeper.models import GateKeeper
from rest_framework.test import APIClient
from testing.testcases import TestCase
from friendships.hbase_models import HBaseFollowing

cache = caches['testing'] if settings.TESTING else caches['default']

FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'
LIST_FOLLOWERS_URL = '/api/friendships/'
LIST_FOLLOWINGS_URL = '/api/friendships/'
FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'


class FriendshipTest(TestCase):

    def setUp(self, hbase_on=False):
        super(FriendshipTest, self).setUp()
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
        self.create_friendship(from_user=self.user1, to_user=self.user2)
        self.create_friendship(from_user=self.user1, to_user=self.user3)
        self.create_friendship(from_user=self.user2, to_user=self.user1)
        self.create_friendship(from_user=self.user3, to_user=self.user2)

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
        # test follow with MySQL
        self._test_follow()
        # test follow with HBase
        self.clear_cache()
        GateKeeper.set_kv('switch_friendship_to_hbase', 'percent', 100)
        self._test_follow()

    def _test_follow(self):
        # only allow POST method
        response = self.user2_client.get(FOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 405)
        # anonymous client not allowed
        response = self.anonymous_client.post(FOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 403)
        # follow non-existed user
        # user_id 999 not exists
        response = self.user2_client.post(FOLLOW_URL.format(999))
        self.assertEqual(response.status_code, 404)
        # not support follow myself
        response = self.user2_client.post(FOLLOW_URL.format(self.user2.id))
        self.assertEqual(response.status_code, 201)
        # follow
        before_count = FriendshipService.get_following_count(self.user2.id)
        response = self.user2_client.post(FOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['friendship']['from_user_id'], self.user2.id)
        self.assertEqual(response.data['friendship']['to_user_id'], self.user3.id)
        after_count = FriendshipService.get_following_count(self.user2.id)
        self.assertEqual(before_count + 1, after_count)
        # re-follow throws error
        before_count = FriendshipService.get_following_count(self.user2.id)
        response = self.user2_client.post(FOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['duplicated'], True)
        after_count = FriendshipService.get_following_count(self.user2.id)
        self.assertEqual(before_count, after_count)

    def test_unfollow_in_MySQL(self):
        # test with MySQL
        self._test_unfollow()

    def test_unfollow_in_HBase(self):
        # TODO: format unfollow test in a more elegant way
        # warnings: friendships are firstly created in MySQL
        # friendships created in setup
        # test with HBase
        # GateKeeper.set_kv('switch_friendship_to_hbase', 'percent', 100)
        self._test_unfollow()

    def _test_unfollow(self):
        # only allow POST method
        response = self.user2_client.get(UNFOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 405)
        # anonymous client not allowed
        response = self.anonymous_client.post(UNFOLLOW_URL.format(self.user3.id))
        self.assertEqual(response.status_code, 403)
        # unfollow non-existed user, user_id 999 not exists
        response = self.user2_client.post(UNFOLLOW_URL.format(999))
        self.assertEqual(response.status_code, 404)
        # not support unfollow myself
        response = self.user2_client.post(UNFOLLOW_URL.format(self.user2.id))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['message'], "You cannot unfollow yourself.")

        fs = HBaseFollowing.filter()
        for f in fs:
            print(f.from_user_id, f.created_at, '->', f.to_user_id)

        # unfollow
        before_count = FriendshipService.get_following_count(self.user2.id)
        response = self.user2_client.post(UNFOLLOW_URL.format(self.user1.id))
        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(int(response.data['deleted']), 1)
        after_count = FriendshipService.get_following_count(self.user2.id)
        self.assertEqual(before_count - 1, after_count)
        # re-unfollow
        before_count = FriendshipService.get_following_count(self.user2.id)
        response = self.user2_client.post(UNFOLLOW_URL.format(self.user1.id))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, 'Friendship not exists')
        after_count = FriendshipService.get_following_count(self.user2.id)
        self.assertEqual(before_count, after_count)


class FriendShipPaginationTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')
        self.user3, self.user3_client = self.create_user_and_client(username='user3')
        # dummy friendship
        self.create_friendship(from_user=self.user1, to_user=self.user2)
        self.create_friendship(from_user=self.user2, to_user=self.user1)
        self.create_friendship(from_user=self.user3, to_user=self.user1)
        self.create_friendship(from_user=self.user2, to_user=self.user3)
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
            self.create_friendship(
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