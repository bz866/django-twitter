from testing.testcases import TestCase
from accounts.models import UserProfile
from accounts.services import UserService


class UserProfileModelTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        self.user1 = self.create_user(username='user1')
        self.user2 = self.create_user(username='user2')

    def test_user_profile(self):
        self.assertEqual(UserProfile.objects.count(), 0)
        # create user profile by accessing attribute
        self.user1.profile
        self.assertEqual(UserProfile.objects.count(), 1)
        # extract profile if exists
        self.user1.profile
        self.assertEqual(UserProfile.objects.count(), 1)
        # create by django objects
        profile = UserProfile.objects.create(user=self.user2)
        self.assertEqual(UserProfile.objects.count(), 2)
        self.assertEqual(profile, self.user2.profile)

    def test_get_user_and_profile_through_cache(self):
        UserService.invalidate_user_cache(user_id=self.user1.id)
        UserService.invalidate_user_cache(user_id=self.user2.id)
        user1 = UserService.get_user_through_cache(self.user1.id)
        profile1 = UserService.get_profile_through_cache(self.user1.id)
        self.assertEqual(user1.id, profile1.user_id)
        UserService.invalidate_profile_cache(self.user1.id)
        profile1 = UserService.get_profile_through_cache(self.user1.id)