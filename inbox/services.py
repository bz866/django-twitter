from notifications.signals import notify
from django.contrib.contenttypes.fields import ContentType
from comments.models import Comment
from tweets.models import Tweet


class NotificationService:

    @classmethod
    def send_like_notification(cls, like):
        target = like.content_object
        # no notifications if like self-owned objects
        if target.user == like.user:
            return
        if like.content_type == ContentType.objects.get_for_model(Comment):
            notify.send(
                sender=like.user,
                recipient=target.user,
                verb='liked your comment',
                action_object=like,
                target=target,
            )
        elif like.content_type == ContentType.objects.get_for_model(Tweet):
            notify.send(
                sender=like.user,
                recipient=target.user,
                verb='liked your tweet',
                action_object=like,
                target=target,
            )
        return

    @classmethod
    def send_comment_notification(cls, comment):
        # no notifications if comment self-owned tweet
        if comment.user == comment.tweet.user:
            return
        notify.send(
            sender=comment.user,
            recipient=comment.tweet.user,
            verb='commented your tweet',
            action_object=comment,
            target=comment.tweet,
        )
