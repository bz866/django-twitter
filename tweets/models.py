import django.db.models
from django.contrib.auth.models import User
from django.db import models
from utils.time_helper import (
    utc_now,
)
from datetime import datetime


# Create your models here.
class Tweet(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(max_length=140)

    class Meta:
        ordering = [
            ["user", "-created_at"],
        ]
        index_together = [
            ['user', 'created_at'],
        ]

    def hours_to_now(self):
        # no timezone information from datetime.now()
        return (utc_now() - self.created_at).seconds // 3600

    def __str__(self):
        return f'{self.user} {self.created_at}: {self.content}'
