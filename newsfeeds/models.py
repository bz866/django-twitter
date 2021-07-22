from django.contrib.auth.models import User
from django.db import models
from tweets.models import Tweet
from utils.memcached_helpers import MemcachedHelper
from django.db.models.signals import pre_delete, post_save
from utils.listeners import invalidate_object_cache


# Create your models here.
class NewsFeed(models.Model):
    # user here is the user to receive the tweet, NOT the user who posts the tweet
    user = models.ForeignKey(to=User, on_delete=models.SET_NULL, null=True)
    tweet = models.ForeignKey(to=Tweet, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = (('user', 'created_at'), )
        unique_together = (('user', 'tweet'), )
        ordering = ('-created_at', )

    def __str__(self):
        return f'{self.created_at} inbox of {self.user}: {self.tweet}'

    @property
    def cached_tweet(self):
        return MemcachedHelper.get_object_throught_cache(Tweet, self.tweet_id)

