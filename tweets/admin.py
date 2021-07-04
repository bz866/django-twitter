from django.contrib import admin
from tweets.models import Tweet


# Register your models here.
@admin.register(Tweet)
class TweetsAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'created_at',
        'user',
        'content',
    )