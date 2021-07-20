from testing.testcases import TestCase
from friendships.models import Friendship
from friendships.services import FriendshipService


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




