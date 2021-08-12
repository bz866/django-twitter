from django.conf import settings
from django.core.cache import caches
from friendships.models import Friendship
from utils.cache import FOLLOWING_PATTERN
from gatekeeper.models import GateKeeper
from utils.time_helper import ts_now_as_int
from friendships.hbase_models import HBaseFollowing, HBaseFollower

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
    def get_follower_ids(cls, user_id):
        friendships = Friendship.objects.filter(to_user_id=user_id)
        return [f.from_user_id for f in friendships]

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

    @classmethod
    def follow(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return None

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            return Friendship.objects.create(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
            )

        now = ts_now_as_int()
        HBaseFollower.create(
            from_user_id=from_user_id,
            created_at=now,
            to_user_id=to_user_id,
        )
        return HBaseFollowing.create(
            from_user_id=from_user_id,
            created_at=now,
            to_user_id=to_user_id,
        )

    @classmethod
    def unfollow(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return 0

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            delete, _ = Friendship.objects.filter(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
            ).delete()
            return delete

        following = cls.get_following_instance(from_user_id=from_user_id, to_user_id=to_user_id)
        # fs = HBaseFollowing.filter(prefix=(from_user_id, None))
        # for f in fs:
        #     print(f.from_user_id, f.created_at, '->',  f.to_user_id)
        # print(following)
        if following is None:
            return 0
        HBaseFollowing.delete(from_user_id=from_user_id, created_at=following.created_at)
        HBaseFollower.delete(to_user_id=to_user_id, created_at=following.created_at)
        return 1

    @classmethod
    def get_following_instance(cls, from_user_id, to_user_id):
        followings = HBaseFollowing.filter(prefix=(from_user_id, None))
        for following in followings:
            if following.to_user_id == to_user_id:
                return following
        return None

    @classmethod
    def has_followed(cls, from_user_id, to_user_id):
        if from_user_id == to_user_id:
            return True

        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            return Friendship.objects.filter(
                from_user_id=from_user_id,
                to_user_id=to_user_id,
            ).exists()

        instance = cls.get_following_instance(from_user_id, to_user_id)
        return instance is not None

    @classmethod
    def get_following_count(cls, from_user_id):
        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            return Friendship.objects.filter(from_user_id=from_user_id).count()
        followings = HBaseFollowing.filter(prefix=(from_user_id, None))
        return len(followings)

    @classmethod
    def get_follower_count(cls, to_user_id):
        if not GateKeeper.is_switch_on('switch_friendship_to_hbase'):
            return Friendship.objects.filter(to_user_id=to_user_id).count()
        followers = HBaseFollower.filter(prefix=(to_user_id, None))
        return len(followers)

