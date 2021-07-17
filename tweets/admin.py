from django.contrib import admin
from tweets.models import Tweet
from tweets.models import TweetPhoto


@admin.register(Tweet)
class TweetsAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'created_at',
        'user',
        'content',
    )


@admin.register(TweetPhoto)
class TweetPhotosAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'user_id',
        'tweet_id',
        'created_at',
        'status',
        'has_deleted',
        'deleted_at',
        'file',
        'order',
    )
    list_filter = ('status', 'has_deleted',)

