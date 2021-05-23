from friendships.models import Friendship
from django.contrib.auth.models import User


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
