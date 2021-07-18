from tweets.models import TweetPhoto


class TweetService:
    @classmethod
    def create_photos_from_files(cls, user, tweet, files):
        photos = []
        for index, file in enumerate(files):
            photo = TweetPhoto(
                user=user,
                tweet=tweet,
                file=file,
                order=index,
            )
            photos.append(photo)
        TweetPhoto.objects.bulk_create(photos)


