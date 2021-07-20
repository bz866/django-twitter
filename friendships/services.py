from django.conf import settings
from django.core.cache import caches
from friendships.models import Friendship
from utils.cache import FOLLOWING_PATTERN

cache = caches['testing'] if settings.TESTING else caches['default']


class FriendshipService():

    def get_followers(self, user):
        # N+1 query wrong way
        # friendships = Friendship.objects.filter(to_user=user)
        # followers = [friendship.from_user for friendship in friendships] # N+1 Query

        # objects query translated as JOIN in compiling
        # friendships = Friendship.objects.filter(
        #     to_user=user
        # ).select_related('from_user') # .selected_related results JOIN in SQL Query
        # followers = [friendship.from_user for friendship in friendships]

        # Use from_user_id to avoid the JOIN, user_id doesn't trigger immidiate DB query
        # friendships = Friendship.objects.filter(to_user=user)
        # followers_ids= [friendship.from_user_id for friendship in friendships]
        # followers = [User.objects.filter(id=id) for id in followers_ids]
        # followers = User.objects.filter(id__in=followers_ids)

        # Use prefetch in production
        # no join, no N+1 query
        friendships = Friendship.objects.filter(
            to_user=user
        ).prefetch_related('from_user')
        followers = [friendship.from_user for friendship in friendships]
        return followers

    @classmethod
    def has_followed(cls, from_user, to_user):
        return Friendship.objects.filter(
            from_user=from_user,
            to_user=to_user,
        ).exists()

    @classmethod
    def get_following_user_id_set(cls, from_user_id):
        key = FOLLOWING_PATTERN.format(user_id=from_user_id)
        user_id_set = cache.get(key)
        # set exists in cache
        if user_id_set is not None:
            return user_id_set
        # set doesn't exist in cache, build one from the DB
        friendships = Friendship.objects.filter(from_user_id=from_user_id)
        user_id_set = set([
            fs.to_user_id
            for fs in friendships
        ])
        cache.set(key, user_id_set) # save in cache
        return user_id_set

    @classmethod
    def invalidate_following_cache(cls, from_user_id):
        key = FOLLOWING_PATTERN.format(user_id=from_user_id)
        cache.delete(key)
