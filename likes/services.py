from likes.models import Like
from django.contrib.contenttypes.fields import ContentType


class LikeService():

    @classmethod
    def get_has_liked(cls, user, obj):
        if user.is_anonymous:
            return False
        return Like.objects.filter(
            user=user,
            object_id=obj.id,
            content_type=ContentType.objects.get_for_model(obj.__class__),
        ).exists()