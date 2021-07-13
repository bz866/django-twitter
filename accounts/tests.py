from testing.testcases import TestCase
from accounts.models import UserProfile


class UserProfileModelTest(TestCase):

    def setUp(self) -> None:
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