from testing.testcases import TestCase
from friendships.models import Friendship
from friendships.services import FriendshipService
from friendships.hbase_models import HBaseFollowing, HBaseFollower
import time
from django_hbase.models import BadRowKeyException, EmptyColumnException


class FriendShipServiceTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        self.user1 = self.create_user(username='user1')
        self.user2 = self.create_user(username='user2')
        self.user3 = self.create_user(username='user3')
        # dummy friendship
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        Friendship.objects.create(from_user=self.user2, to_user=self.user1)
        Friendship.objects.create(from_user=self.user3, to_user=self.user1)
        Friendship.objects.create(from_user=self.user2, to_user=self.user3)
        #          user1
        #       /*       *\\
        #     /          \\*
        #     user3   *--  user2

    def test_get_following_user_id_set(self):
        FriendshipService.invalidate_following_cache(from_user_id=self.user2.id)
        user_id_set_2 = FriendshipService.get_following_user_id_set(self.user2.id)
        self.assertEqual(user_id_set_2, {self.user1.id, self.user3.id})
        user_id_set_1 = FriendshipService.get_following_user_id_set(self.user1.id)
        self.assertEqual(user_id_set_1, {self.user2.id})

        Friendship.objects.filter(
            from_user=self.user2,
            to_user=self.user3,
        ).delete()
        Friendship.objects.filter(
            from_user=self.user1,
            to_user=self.user2,
        ).delete()
        # mannually clear the cache
        FriendshipService.invalidate_following_cache(from_user_id=self.user2.id)
        user_id_set_2 = FriendshipService.get_following_user_id_set(self.user2.id)
        self.assertEqual(user_id_set_2, {self.user1.id})
        # cache automatically cleared in delete() by listener
        user_id_set_1 = FriendshipService.get_following_user_id_set(self.user1.id)
        self.assertEqual(len(user_id_set_1), 0)
        # cache automatically cleared in create() by listener
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user3
        )
        user_id_set_1 = FriendshipService.get_following_user_id_set(self.user1.id)
        self.assertEqual(user_id_set_1, {self.user3.id})


class HBaseFriendshipTest(TestCase):

    def setUp(self) -> None:
        super(HBaseFriendshipTest, self).setUp()

    def ts_now(self):
        return int(time.time() * 1000000)

    def test_save_and_get(self):
        now = self.ts_now()
        following = HBaseFollowing(
            from_user_id=123,
            created_at=now,
            to_user_id=456,
        )
        following.save()
        following = HBaseFollowing.get(from_user_id=123, created_at=now)
        self.assertEqual(following.from_user_id, 123)
        self.assertEqual(following.created_at, now)
        self.assertEqual(following.to_user_id, 456)

        following.to_user_id = 789
        following.save()
        self.assertEqual(following.to_user_id, 789)
        following = HBaseFollowing.get(from_user_id=123, created_at=now)
        self.assertEqual(following.to_user_id, 789)

        # get non-exist object get none
        following = HBaseFollowing.get(
            from_user_id=123,
            created_at=self.ts_now()
        )
        self.assertIsNone(following)

        # wrong row_keys to creat
        try:
            following = HBaseFollowing(from_user_id=123, to_user_id=456)
            following.save()
            exception_raised = False
        except BadRowKeyException as e:
            exception_raised = True
            self.assertEqual(str(e), 'created_at not defined')
        self.assertEqual(exception_raised, True)

    def test_create_and_get(self):
        now = self.ts_now()
        HBaseFollower.create(
            created_at=now,
            to_user_id=456,
            from_user_id=123,
        )
        follower = HBaseFollower.get(to_user_id=456, created_at=now)
        print("FOLLOWER: ", follower.__dict__)
        self.assertEqual(follower.from_user_id, 123)
        self.assertEqual(follower.to_user_id, 456)
        self.assertEqual(follower.created_at, now)

        # invalid row_key get
        try:
            HBaseFollower.get(to_user_id=456, from_user_id=123)
            exception_raised = False
        except BadRowKeyException as e:
            exception_raised = True
            self.assertEqual(str(e), "created_at not defined")
        self.assertEqual(exception_raised, True)

        # invalid row_keys creation
        try:
            HBaseFollower.create(from_user_id=123, create_at=now)
            exception_raised = False
        except BadRowKeyException as e:
            exception_raised = True
            self.assertEqual(str(e), 'to_user_id not defined')
        self.assertEqual(exception_raised, True)

        # no column_key value
        try:
            HBaseFollower.create(to_user_id=123, created_at=now)
            exception_raised = False
        except EmptyColumnException as e:
            exception_raised = True
        self.assertEqual(exception_raised, True)

        # row_key should not have ':'
        try:
            HBaseFollower.create(
                from_user_id=123,
                created_at=now,
                to_user_id='456:',
            )
            exception_raised = False
        except BadRowKeyException as e:
            exception_raised = True
            self.assertEqual(str(e), "to_user_id must not have ':' in value 456:")
        self.assertEqual(exception_raised, True)





