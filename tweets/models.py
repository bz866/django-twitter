from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import ContentType
from django.db import models
from django.db.models.signals import post_save
from likes.models import Like
from tweets.constants import TWEET_PHOTO_STAUS_CHOICES, TweetPhotoStatus
from utils.listeners import invalidate_object_cache
from utils.time_helper import utc_now
from utils.memcached_helpers import MemcachedHelper
from tweets.listeners import push_tweet_to_cache


class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(max_length=140)

    # denormalized counts for efficiently accessing, avoid N+1 query problem
    # fields must have null=True to avoid table being locked
    # otherwise, the db lock the whole tables in migrations
    # have another script to fill counts for old posts
    # db will only have row lock in
    comment_count = models.IntegerField(default=0, null=True)
    like_count = models.IntegerField(default=0, null=True)

    class Meta:
        index_together = [
            ['user', 'created_at'],
        ]
        ordering = ['user', '-created_at']

    @property
    def hours_to_now(self):
        # no timezone information from datetime.now()
        return (utc_now() - self.created_at).seconds // 3600

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Tweet),
            object_id=self.id,
        ).order_by('created_at')

    def __str__(self):
        return f'{self.created_at} {self.user}: {self.content}'

    @property
    def cached_user(self):
        return MemcachedHelper.get_object_throught_cache(User, self.user_id)


class TweetPhoto(models.Model):
    # tweet and user as foreign key benefit for backtrack
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    # backtrack user photos for user behavior examinations
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    # status, PENDING, ACTIVE, DELETED
    status = models.IntegerField(
        choices=TWEET_PHOTO_STAUS_CHOICES,
        default=TweetPhotoStatus.PENDING,
    )
    # file content
    file = models.FileField()
    order = models.IntegerField(default=0)

    has_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # index together based on query scenarios
        index_together = (
            ('user', 'created_at'),
            ('has_deleted', 'created_at'),
            ('status', 'created_at'),
            ('tweet', 'order'),
        )

    def __str__(self):
        return f'{self.user_id} {self.tweet_id} : {self.file}'


# clear cache in create()
post_save.connect(invalidate_object_cache, sender=Tweet)
# clear redis cache in create()
post_save.connect(push_tweet_to_cache, sender=Tweet)
