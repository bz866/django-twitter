from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from tweets.models import Tweet


class TestCase(DjangoTestCase):

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
