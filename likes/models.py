from accounts.services import UserService
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models


class Like(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
    )
    # created_at: user liked content_object
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # for searching user liked posts
        unique_together = (('user', 'content_type', 'object_id'),)
        # search all likes of a post, order by created_at
        index_together = (('content_type', 'object_id', 'created_at'),)

    def __str__(self):
        return f'{self.created_at} {self.user} liked {self.content_type} {self.object_id}'

    @property
    def cached_user(self):
        return UserService.get_user_through_cache(self.user_id)

