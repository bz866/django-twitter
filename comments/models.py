from django.db import models
from django.contrib.auth.models import User
from tweets.models import Tweet
from likes.models import Like
from django.contrib.contenttypes.fields import ContentType


# Create your models here.
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tweet = models.ForeignKey(Tweet, on_delete=models.SET_NULL, null=True)
    content = models.TextField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True) # updates on creation only
    updated_at = models.DateTimeField(auto_now=True) # take precedence, updates field each time

    class Meta:
        index_together = (('tweet', 'created_at'), )
        ordering = ('tweet', 'created_at')

    @property
    def like_set(self):
        return Like.objects.filter(
            content_type=ContentType.objects.get_for_model(Comment),
            object_id=self.id,
        ).order_by('created_at')

    def __str__(self):
        return f'{self.created_at}\n Under {self.tweet_id}\n @{self.user}\n comments: {self.content}'