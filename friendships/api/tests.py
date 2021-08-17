from django.conf import settings
from django.core.cache import caches
from friendships.services import FriendshipService
from gatekeeper.models import GateKeeper
from testing.testcases import TestCase
from friendships.hbase_models import HBaseFollowing
from utils.time_helper import ts_now_as_int
from utils.paginations import EndlessPagination

cache = caches['testing'] if settings.TESTING else caches['default']

FOLLOWERS_URL = '/api/friendships/{}/followers/'
FOLLOWINGS_URL = '/api/friendships/{}/followings/'
LIST_FOLLOWERS_URL = '/api/friendships/'
LIST_FOLLOWINGS_URL = '/api/friendships/'
FOLLOW_URL = '/api/friendships/{}/follow/'
UNFOLLOW_URL = '/api/friendships/{}/unfollow/'


class FriendshipTest(TestCase):

    def setUp(self):
        super(FriendshipTest, self).setUp()
        # dummy users
        self.user1, self.user1_client = self.create_user_and_client(username='username1')
        self.user2, self.user2_client = self.create_user_and_client(username='username2')
        self.user3, self.user3_client = self.create_user_and_client(username='username3')

    def _create_dummy_friendship(self):
        # dummy friendships
        self.create_friendship(from_user=self.user1, to_user=self.user2)
        self.create_friendship(from_user=self.user1, to_user=self.user3)
        self.create_friendship(from_user=self.user2, to_user=self.user1)
        self.create_friendship(from_user=self.user3, to_user=self.user2)

    def test_get_followers(self):
        self._create_dummy_friendship()
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
        self._create_dummy_friendship()
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
        self._create_dummy_friendship()
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
        self._create_dummy_friendship()
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
        # test with HBase
        GateKeeper.set_kv('switch_friendship_to_hbase', 'percent', 100)
        self._test_unfollow()

    def _test_unfollow(self):
        self._create_dummy_friendship()
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
        # unfollow
        before_count = FriendshipService.get_following_count(self.user2.id)
        response = self.user2_client.post(UNFOLLOW_URL.format(self.user1.id))
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


class FriendshipPaginationTest(TestCase):
    # TODO: HBase test is way to slow

    def setUp(self) -> None:
        super(FriendshipPaginationTest, self).setUp()
        GateKeeper.set_kv('switch_friendship_to_hbase', 'percent', 100)
        self.linghu, self.linghu_client = self.create_user_and_client(username='linghu')
        self.dongxie, self.dongxie_client = self.create_user_and_client(username='dongxie')

        # create followings and followers for dongxie
        for i in range(2):
            follower = self.create_user('dongxie_follower{}'.format(i))
            self.create_friendship(from_user=follower, to_user=self.dongxie)
        for i in range(3):
            following = self.create_user('dongxie_following{}'.format(i))
            self.create_friendship(from_user=self.dongxie, to_user=following)

    # def _paginate_to_get_friendships(self, client, url):
    #     response = client.get(url)
    #     friendships = response.data['results']
    #     while response.data['has_next_page']:
    #         response = client.get(url, {
    #             'created_at__lt': friendships[-1]['created_at']
    #         })
    #         friendships.extend(response.data['results'])
    #     return friendships
    #
    # def _test_followings_pagination(self):
    #     self.user1, self.user1_client = self.create_user_and_client(username='user1')
    #     self.user2, self.user2_client = self.create_user_and_client(username='user2')
    #     user2_followings = []
    #     for i in range(31, 61):
    #         user2_followings.append(
    #             self.create_friendship(
    #                 from_user=self.user2,
    #                 to_user=self.create_user(username=f'user{i}'),
    #             )
    #         )
    #         user2_followings = user2_followings[::-1]
    #
    #     paginate_followings = self._paginate_to_get_friendships(
    #         client=self.user1_client,
    #         url=FOLLOWINGS_URL.format(self.user2.id),
    #     )
    #     self.assertEqual(len(user2_followings), len(paginate_followings))
    #     for i in range(len(user2_followings)):
    #         self.assertEqual(user2_followings[i].from_user_id, paginate_followings[i]['from_user_id'])
    #         self.assertEqual(user2_followings[i].to_user_id, paginate_followings[i]['to_user_id'])
    #         self.assertEqual(user2_followings[i].created_at, paginate_followings[i]['created_at'])
    #
    #     # new friendship
    #     new_user2_followings = []
    #     for i in range(61, 71):
    #         new_user2_followings.append(
    #             self.create_friendship(
    #                 from_user=self.user2,
    #                 to_user=self.create_user(username=f'user{i}'),
    #             )
    #         )
    #         new_user2_followings = new_user2_followings[::-1]
    #     paginate_followings = self.user1_client.get(
    #         FOLLOWINGS_URL.format(self.user2.id),
    #         {'created_at__gt': user2_followings[0].created_at}
    #     )
    #     self.assertEqual(len(new_user2_followings), len(paginate_followings))
    #     for i in range(len(new_user2_followings)):
    #         self.assertEqual(new_user2_followings[i].from_user_id, paginate_followings[i]['from_user_id'])
    #         self.assertEqual(new_user2_followings[i].to_user_id, paginate_followings[i]['to_user_id'])
    #         self.assertEqual(new_user2_followings[i].created_at, paginate_followings[i]['created_at'])
    #
    # def test_friendship_pagination(self):
    #     self._test_followings_pagination()

    def test_followers(self):
        url = FOLLOWERS_URL.format(self.dongxie.id)
        # post is not allowed
        response = self.anonymous_client.post(url)
        self.assertEqual(response.status_code, 405)
        # get is ok
        response = self.anonymous_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        # 确保按照时间倒序
        ts0 = response.data['results'][0]['created_at']
        ts1 = response.data['results'][1]['created_at']
        self.assertEqual(ts0 > ts1, True)
        self.assertEqual(
            response.data['results'][0]['user']['username'],
            'dongxie_follower1',
        )
        self.assertEqual(
            response.data['results'][1]['user']['username'],
            'dongxie_follower0',
        )

    def test_followers_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            follower = self.create_user('linghu_follower{}'.format(i))
            friendship = self.create_friendship(from_user=follower,
                                                to_user=self.linghu)
            friendships.append(friendship)
            if follower.id % 2 == 0:
                self.create_friendship(from_user=self.dongxie, to_user=follower)

        url = FOLLOWERS_URL.format(self.linghu.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # dongxie has followed users with even id
        response = self.dongxie_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

    def test_followings_pagination(self):
        page_size = EndlessPagination.page_size
        friendships = []
        for i in range(page_size * 2):
            following = self.create_user('linghu_following{}'.format(i))
            friendship = self.create_friendship(from_user=self.linghu,
                                                to_user=following)
            friendships.append(friendship)
            if following.id % 2 == 0:
                self.create_friendship(from_user=self.dongxie,
                                       to_user=following)

        url = FOLLOWINGS_URL.format(self.linghu.id)
        self._paginate_until_the_end(url, 2, friendships)

        # anonymous hasn't followed any users
        response = self.anonymous_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], False)

        # dongxie has followed users with even id
        response = self.dongxie_client.get(url)
        for result in response.data['results']:
            has_followed = (result['user']['id'] % 2 == 0)
            self.assertEqual(result['has_followed'], has_followed)

        # linghu has followed all his following users
        response = self.linghu_client.get(url)
        for result in response.data['results']:
            self.assertEqual(result['has_followed'], True)

        # test pull new friendships
        last_created_at = friendships[-1].created_at
        response = self.linghu_client.get(url,
                                          {'created_at__gt': last_created_at})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

        new_friends = [self.create_user('big_v{}'.format(i)) for i in range(3)]
        new_friendships = []
        for friend in new_friends:
            new_friendships.append(
                self.create_friendship(from_user=self.linghu, to_user=friend))
        response = self.linghu_client.get(url,
                                          {'created_at__gt': last_created_at})
        self.assertEqual(len(response.data['results']), 3)
        for result, friendship in zip(response.data['results'],
                                      reversed(new_friendships)):
            self.assertEqual(result['created_at'], friendship.created_at)

    def _paginate_until_the_end(self, url, expect_pages, friendships):
        results, pages = [], 0
        response = self.anonymous_client.get(url)
        results.extend(response.data['results'])
        pages += 1
        while response.data['has_next_page']:
            self.assertEqual(response.status_code, 200)
            last_item = response.data['results'][-1]
            response = self.anonymous_client.get(url, {
                'created_at__lt': last_item['created_at'],
            })
            results.extend(response.data['results'])
            pages += 1

        self.assertEqual(len(results), len(friendships))
        self.assertEqual(pages, expect_pages)
        # friendship is in ascending order, results is in descending order
        for result, friendship in zip(results, friendships[::-1]):
            self.assertEqual(result['created_at'], friendship.created_at)
