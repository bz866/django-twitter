from comments.models import Comment
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import ContentType
from django.core.cache import caches
from django.test import TestCase as DjangoTestCase
from django_hbase.client import HBaseClient
from django_hbase.models import HBaseModel
from friendships.models import Friendship
from friendships.services import FriendshipService
from likes.models import Like
from newsfeeds.models import NewsFeed
from rest_framework.test import APIClient
from tweets.models import Tweet
from utils.redis_client import RedisClient
from gatekeeper.models import GateKeeper


class TestCase(DjangoTestCase):
    hbase_tables_created = False

    def setUp(self) -> None:
        self.clear_cache()
        try:
            self.hbase_tables_created = True
            for hbase_model_class in HBaseModel.__subclasses__():
                hbase_model_class.create_table()
        except Exception as e:
            self.tearDown()
            raise e

    def tearDown(self) -> None:
        if not self.hbase_tables_created:
            return
        for hbase_model_class in HBaseModel.__subclasses__():
            hbase_model_class.drop_table()

    def clear_cache(self):
        caches['testing'].clear()
        RedisClient.clear()

    def clear_hbase(self):
        HBaseClient.clear_all_tables()

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
        return FriendshipService.follow(from_user_id=from_user.id, to_user_id=to_user.id)

    def create_newsfeed(self, user, tweet):
        return NewsFeed.objects.create(
            user=user,
            tweet=tweet,
        )

