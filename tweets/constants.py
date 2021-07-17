class TweetPhotoStatus:
    PENDING = 0
    ACTIVE = 1
    DELETED = 2


TWEET_PHOTO_STAUS_CHOICES = (
    (TweetPhotoStatus.PENDING, 'Pending'),
    (TweetPhotoStatus.ACTIVE, 'Active'),
    (TweetPhotoStatus.DELETED, 'Deleted'),
)

