from tweets.models import Tweet
from accounts.api.serializers import UserSerializerForTweet
from comments.api.serializers import CommentSerializerForTweet
from rest_framework import serializers
from likes.services import LikeService
from tweets.services import TweetService
from rest_framework.exceptions import ValidationError
from tweets.constants import TWEET_PHOTOS_UPLOAD_LIMIT


class TweetSerializer(serializers.ModelSerializer):
    user = UserSerializerForTweet(source='cached_user')
    comment_count = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    has_liked = serializers.SerializerMethodField()
    photo_urls = serializers.SerializerMethodField()

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comment_count',
            'like_count',
            'has_liked',
            'photo_urls',
        )

    def get_like_count(self, obj):
        # # call like_set using like_set @property in Tweet model
        # return obj.like_set.count()
        # get count from denormalized count
        return obj.like_count

    def get_comment_count(self, obj):
        # # call comment_set using the comment ForeignKey in Tweet model
        # # django default backward FOO_set retrieving objects
        # return obj.comment_set.count()
        # get count from denormalized count
        return obj.comment_count

    def get_has_liked(self, obj):
        user = self.context['request'].user
        return LikeService.get_has_liked(user, obj)

    def get_photo_urls(self, obj):
        photo_urls = []
        for photo in obj.tweetphoto_set.all().order_by('order'):
            photo_urls.append(photo.file.url)
        return photo_urls


class TweetSerializerForDetail(TweetSerializer):
    user = UserSerializerForTweet(source='cached_user')
    comments = CommentSerializerForTweet(source='comment_set', many=True)

    class Meta:
        model = Tweet
        fields = (
            'id',
            'user',
            'created_at',
            'content',
            'comments',
            'comment_count',
            'like_count',
            'has_liked',
            'photo_urls',
        )


class TweetCreateSerializer(serializers.ModelSerializer):
    content = serializers.CharField(min_length=6, max_length=140)
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=True,
        required=False,
    )

    class Meta:
        model = Tweet
        fields = ('content', 'files',)

    def validate(self, attrs):
        if len(attrs.get('files', [])) > TWEET_PHOTOS_UPLOAD_LIMIT:
            raise ValidationError({
                'message': f'you can upload {TWEET_PHOTOS_UPLOAD_LIMIT} photos '
                           f'at most '
            })
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        content = validated_data['content']
        tweet = Tweet.objects.create(user=user, content=content)
        if validated_data.get('files'):
            TweetService.create_photos_from_files(
                user=user,
                tweet=tweet,
                files=validated_data['files'],
            )
        return tweet

