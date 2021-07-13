from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    # One to One field to User
    # User works like a foreign key to build connection
    # one to one works like unique together to ensure one-to-one mapping between the User and UserProfile
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True)
    avatar = models.FileField(null=True)
    nickname = models.CharField(null=True, max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.created_at} User {self.user.id} ({self.nickname}) created user profile.'


def get_profile(user):
    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    setattr(user, '_cached_user_profile', profile)
    return profile


# add UserProfile to User model dynamically
User.profile = property(get_profile)
