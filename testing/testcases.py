from comments.models import Comment
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import ContentType
from django.core.cache import caches
from django.test import TestCase as DjangoTestCase
from likes.models import Like
from newsfeeds.models import NewsFeed
from rest_framework.test import APIClient
from tweets.models import Tweet
from friendships.models import Friendship
from utils.redis_client import RedisClient


class TestCase(DjangoTestCase):

    def clear_cache(self):
        caches['testing'].clear()
        RedisClient.clear()

    @property
    def anonymous_client(self):
        if hasattr(self, '_anonymous_client'):
            return self._anonymous_client
        self._anonymous_client = APIClient()
        return self._anonymous_client

    def create_user(self, username, email=None, password=None):
        if not email:
            email = f'{username}@email.com'
        if not password:
            password = 'defaultpassword'
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
        )
        return user

    def create_user_and_client(self, username, email=None, password=None):
        user = self.create_user(username, email, password)
        user_client = APIClient()
        user_client.force_authenticate(user=user)
        return user, user_client

    def create_tweet(self, user, content=None):
        if not content:
            content = 'default content'
        tweet = Tweet.objects.create(user=user, content=content)
        return tweet

    def create_comment(self, user, tweet, content=None):
        if not content:
            content = 'default comment content'
        comment = Comment.objects.create(user=user, tweet=tweet, content=content)
        return comment

    def create_like(self, user, object):
        like, _ = Like.objects.get_or_create(
            user=user,
            content_type=ContentType.objects.get_for_model(object.__class__),
            object_id=object.id, 
        )
        return like

    def create_friendship(self, from_user, to_user):
        friendship = Friendship.objects.create(
            from_user=from_user,
            to_user=to_user,
        )
        return friendship

    def create_newsfeed(self, user, tweet):
        newsfeed = NewsFeed.objects.create(
            user=user,
            tweet=tweet,
        )
        return newsfeed
      
