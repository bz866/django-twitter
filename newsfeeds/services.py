from friendships.services import FriendshipService
from newsfeeds.models import NewsFeed


class NewsFeedService():

    def fanout_to_followers(self, tweet):
        # get all followers of the poster
        followers = FriendshipService().get_followers(tweet.user)
        # create newsfeed for all followers
        newsfeeds = [
            NewsFeed(user=follower, tweet=tweet)
            for follower in followers
        ]
        # the poster can see own posted tweet
        newsfeeds.append(NewsFeed(user=tweet.user, tweet=tweet))
        # create objects by batch, more efficiency
        NewsFeed.objects.bulk_create(newsfeeds)

