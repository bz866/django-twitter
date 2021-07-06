from django.contrib.auth.models import User
from django.db import models
from utils.time_helper import utc_now
from likes.models import Like
from django.contrib.contenttypes.fields import ContentType


# Create your models here.
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

