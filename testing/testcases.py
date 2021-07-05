from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from tweets.models import Tweet
from rest_framework.test import APIClient
from likes.models import Like
from django.contrib.contenttypes.fields import ContentType
from comments.models import Comment


class TestCase(DjangoTestCase):

    @property
    def anonymous_client(self):
        if hasattr(self, '_anonymous_client'):
            return self._anonymous_client
        self._anonymous_client = APIClient()
        return self._anonymous_client

    def create_user(self, username, email=None, password=None, *args, **kwargs):
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
      
