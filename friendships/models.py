from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete, post_save
from friendships.listeners import invalidate_following_cache


class Friendship(models.Model):
    from_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='friendship_from_user',
        null=True,
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='friendship_to_user',
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        index_together = [
            ['from_user', 'created_at'],
            ['to_user', 'created_at'],
        ]

        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at} : {self.from_user} -> {self.to_user}'


# for the data consistency between the cache and the db
# delete cache when create() and delete() called
pre_delete.connect(invalidate_following_cache, sender=Friendship)
post_save.connect(invalidate_following_cache, sender=Friendship)

