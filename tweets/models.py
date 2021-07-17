from django.contrib.auth.models import User
from django.db import models
from utils.time_helper import utc_now
from likes.models import Like
from django.contrib.contenttypes.fields import ContentType
from tweets.constants import TWEET_PHOTO_STAUS_CHOICES, TweetPhotoStatus


class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(max_length=140)

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

