from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete, post_save
from accounts.listeners import invalidate_user_cache
from accounts.listeners import invalidate_profile_cache


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


# by adding UserProfile to User model in runtime
# preload UserProfile in memory when calling User
# optimized efficiency by memory access
def get_profile(user):
    from accounts.services import UserService

    if hasattr(user, '_cached_user_profile'):
        return getattr(user, '_cached_user_profile')
    profile = UserService.get_profile_through_cache(user_id=user.id)
    # set profile as a property of user, access profile in memory
    setattr(user, '_cached_user_profile', profile)
    return profile


# add UserProfile to User model dynamically
User.profile = property(get_profile)

# clear cache for User in create() and delete()
pre_delete.connect(invalidate_user_cache, sender=User)
post_save.connect(invalidate_user_cache, sender=User)

# clear cache for UserProfile in create() and delete()
pre_delete.connect(invalidate_profile_cache, sender=UserProfile)
post_save.connect(invalidate_profile_cache, sender=UserProfile)
