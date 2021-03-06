from comments.models import Comment
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet
from tweets.models import TweetPhoto
from tweets.services import TweetService
from utils.redis_client import RedisClient

LIST_URL = '/api/tweets/'
CREATE_URL = '/api/tweets/'
RETRIEVE_URL = '/api/tweets/{}/'
TWEET_RETRIEVE_URL = '/api/tweets/{}/'
TWEET_LIST_URL = '/api/tweets/'
COMMENT_LIST_URL = '/api/comments/'
NEWSFEED_LIST_URL = '/api/newsfeeds/'


class TweetTest(TestCase):

    def setUp(self):
        self.clear_cache()
        RedisClient.clear()
        self.user1_client = APIClient()
        self.user1 = self.create_user(username='username1')
        self.user1_client.force_authenticate(user=self.user1)
        self.user1_tweets = [
            self.create_tweet(self.user1, i)
            for i in range(3) # 3 tweets for user_1
        ]

        self.user2_client = APIClient()
        self.user2 = self.create_user(username='username2')
        self.user2_client.force_authenticate(user=self.user2)
        self.user2_tweets = [
            self.create_tweet(self.user2, i)
            for i in range(2) # 2 tweets for user_2
        ]
        self.user3, self.user3_client = self.create_user_and_client(username='username3')

    def test_list(self):
        # need user_id to list all tweets belong to a user
        response = self.anonymous_client.get(LIST_URL)
        self.assertEqual(response.status_code, 400)

        # users have right number of tweets listed
        response = self.user1_client.get(LIST_URL, {'user_id': self.user1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['results'][0]['user']['username'], 'username1')
        response = self.user2_client.get(LIST_URL, {'user_id': self.user2.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['user']['username'], 'username2')

        # tweets should be listed order by created_at in descending order
        response = self.user1_client.get(LIST_URL, {'user_id': self.user1.id})
        self.assertEqual(response.data['results'][0]['id'], self.user1_tweets[2].id)
        self.assertEqual(response.data['results'][1]['id'], self.user1_tweets[1].id)

    def test_create(self):
        # anonymous user can not create tweet
        response = self.anonymous_client.post(CREATE_URL)
        self.assertEqual(response.status_code, 403)

        # too short content
        response = self.user1_client.post(CREATE_URL, {
            'content': 'x'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "Please check the input")
        # too long content
        response = self.user1_client.post(CREATE_URL, {
            'content': '0' * 141
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "Please check the input")

        # create a tweet by user1
        response = self.user1_client.post(CREATE_URL, {
            'content': '0' * 140
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tweet']['content'], '0'*140)
        self.assertEqual(Tweet.objects.count(), 6)
        self.assertEqual(response.data['tweet']['user']['username'], 'username1')

        # create a tweet by user2
        self.user2_client.login(username='username2', password='defaultpassword')
        response = self.user2_client.post(CREATE_URL, {
            'user': self.user2,
            'content': 'default content',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tweet']['content'], "default content")
        self.assertEqual(Tweet.objects.count(), 7)
        self.assertEqual(response.data['tweet']['user']['username'], 'username2')

    def test_retrieve(self):
        dummy_url = RETRIEVE_URL.format(self.user1_tweets[0].id)
        # GET method only
        response = self.user1_client.post(dummy_url)
        self.assertEqual(response.status_code, 405)
        # login users only
        response = self.anonymous_client.get(dummy_url)
        self.assertEqual(response.status_code, 403)
        # access non-exist tweet
        response = self.user1_client.get(RETRIEVE_URL.format(-1))
        self.assertEqual(response.status_code, 404)

        # dummy comments
        user1_comments_own = [
            self.create_comment(self.user1, self.user1_tweets[i])
            for i in range(0, 3)
        ]
        user2_comments_own = [
            self.create_comment(self.user2, self.user2_tweets[i])
            for i in range(1, -1, -1)
        ]
        user1_comments_others = [
            self.create_comment(self.user1, self.user2_tweets[i])
            for i in range(1, -1, -1)
        ]
        # check length of comments of a tweet
        response = self.user2_client.get(RETRIEVE_URL.format(self.user1_tweets[0].id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 1)
        # comments ordered by created_at
        response = self.user1_client.get(RETRIEVE_URL.format(self.user2_tweets[0].id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['comments']), 2)
        self.assertEqual(response.data['comments'][0]['user']['id'], self.user2.id)
        self.assertEqual(response.data['comments'][1]['user']['id'], self.user1.id)
        self.assertLess(
            response.data['comments'][0]['created_at'],
            response.data['comments'][1]['created_at']
        )

    def test_tweet_like(self):
        # dummy tweet
        tweet1 = Tweet.objects.create(
            user=self.user1,
            content='tweet 1 for comment test'
        )
        tweet2 = Tweet.objects.create(
            user=self.user2,
            content='tweet without any comments'
        )
        # dummy comment
        print("COMMENT1 CREATE")
        print()
        comment1 = Comment.objects.create(
            user=self.user1,
            tweet=tweet1,
            content='original comment'
        )
        print("COMMENT2 CREATE")
        print()
        comment2 = Comment.objects.create(
            user=self.user2,
            tweet=tweet1,
            content='original comment'
        )
        comment3 = Comment.objects.create(
            user=self.user1,
            tweet=tweet2,
            content='original comment'
        )

        # create like on comment
        self.create_like(user=self.user1, object=comment1)
        self.create_like(user=self.user2, object=comment2)
        self.create_like(user=self.user2, object=comment1)
        # create like on tweet
        self.create_like(user=self.user2, object=tweet1)
        self.create_like(user=self.user3, object=tweet1)

        # check comment like in Tweet Retrieve
        response = self.user1_client.get(
            TWEET_RETRIEVE_URL.format(tweet1.id)
        )
        self.assertEqual(response.data['has_liked'], False) # tweet1 not liked by user1
        self.assertEqual(response.data['like_count'], 2) # tweet has 2 likes
        self.assertEqual(response.data['comment_count'], 2)
        response = self.user2_client.get(
            TWEET_RETRIEVE_URL.format(tweet1.id)
        )
        self.assertEqual(response.data['comment_count'], 2)

        # check comment like in Tweet LIST
        response = self.user1_client.get(
            TWEET_LIST_URL,
            {'user_id': self.user1.id},
        )
        self.assertEqual(response.data['results'][0]['comment_count'], 2)
        response = self.user2_client.get(
            TWEET_LIST_URL,
            {'user_id': self.user2.id},
        )
        self.assertEqual(response.data['results'][0]['comment_count'], 1)

    def test_create_with_files(self):
        # allow empty file list
        response = self.user1_client.post(CREATE_URL, {
            'content': 'default content',
            'files': [],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 0)

        # allow single file
        dummy_file = SimpleUploadedFile(
            name='sample-image',
            content=str.encode('sample-image'),
            content_type='image/jpeg',
        )
        response = self.user1_client.post(CREATE_URL, {
            'content': 'default content',
            'files': [dummy_file],
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 1)

        # all multiple files
        dummy_files = [
            SimpleUploadedFile(
                name='sample-image-{}.jpg'.format(i),
                content=str.encode('sample-image-{}'.format(i)),
                content_type='image/jpeg',
            )
            for i in range(9)
        ]
        response = self.user1_client.post(CREATE_URL, {
            'content': 'default content',
            'files': dummy_files,
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(TweetPhoto.objects.count(), 10)
        # urls should be in order
        self.assertEqual(len(response.data['tweet']['photo_urls']), 9)
        self.assertTrue('sample-image-0' in response.data['tweet']['photo_urls'][0])
        self.assertTrue('sample-image-1' in response.data['tweet']['photo_urls'][1])

        # allow 9 files at most
        dummy_files = [
            SimpleUploadedFile(
                name='sample-image-{}.jpg'.format(i),
                content=str.encode('sample-image-{}'.format(i)),
                content_type='image/jpeg',
            )
            for i in range(10) # must <= 9
        ]
        response = self.user1_client.post(CREATE_URL, {
            'content': 'default content',
            'files': [dummy_files],
        })
        self.assertEqual(response.status_code, 400)

    def test_retrieve_with_files(self):
        dummy_files = [
            SimpleUploadedFile(
                name='sample-image-{}.jpg'.format(i),
                content=str.encode('sample-image-{}'.format(i)),
                content_type='image/jpeg',
            )
            for i in range(5)
        ]
        response = self.user1_client.post(CREATE_URL, {
            'content': 'default content',
            'files': dummy_files,
        })
        tweet_id = response.data['tweet']['id']

        # retrieve tweet with photo urls
        response = self.user2_client.get(RETRIEVE_URL.format(tweet_id))
        self.assertEqual(len(response.data['photo_urls']), 5)
        self.assertTrue('sample-image-0' in response.data['photo_urls'][0])
        self.assertTrue('sample-image-1' in response.data['photo_urls'][1])


class TweetPaginationTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        RedisClient.clear()
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        # dummy tweets
        self.tweets = []
        self.tweets = [
            self.create_tweet(user=self.user1)
            for i in range(41)
        ]
        self.tweets = self.tweets[::-1] # order by created_at in descending

    def test_tweets_endless_pagination(self):
        response = self.user1_client.get(
            TWEET_LIST_URL,
            {'user_id': self.user1.id}
        )
        self.assertEqual(response.status_code, 200)
        # default first page
        self.assertEqual(len(response.data['results']), 20)
        self.assertTrue(response.data['has_next_page'])
        # tweets list in created_at descending order
        self.assertEqual(response.data['results'][0]['id'], self.tweets[0].id)
        self.assertEqual(response.data['results'][1]['id'], self.tweets[1].id)

        # load to the second page
        response = self.user1_client.get(
            TWEET_LIST_URL,
            {'user_id': self.user1.id, 'created_at__lt': self.tweets[19].created_at},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 20)
        self.assertTrue(response.data['has_next_page'])
        # tweets list in created_at descending order
        self.assertEqual(response.data['results'][0]['id'], self.tweets[20].id)
        self.assertEqual(response.data['results'][1]['id'], self.tweets[21].id)

        # load to the third page
        response = self.user1_client.get(
            TWEET_LIST_URL,
            {'user_id': self.user1.id, 'created_at__lt': self.tweets[39].created_at}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertFalse(response.data['has_next_page'])
        self.assertEqual(response.data['results'][0]['id'], self.tweets[-1].id)
        self.assertEqual(response.data['results'][0]['id'], self.tweets[40].id)

        # dummy new tweets
        new_tweets = [
            self.create_tweet(user=self.user1)
            for i in range(12)
        ]
        new_tweets = new_tweets[::-1]
        all_tweets = new_tweets + self.tweets

        # refresh to have the most recent page
        response = self.user1_client.get(
            TWEET_LIST_URL,
            {'user_id': self.user1.id, 'created_at__gt': self.tweets[0].created_at}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 12)
        self.assertFalse(response.data['has_next_page'])
        self.assertEqual(response.data['results'][0]['id'], all_tweets[0].id)
        self.assertEqual(response.data['results'][1]['id'], all_tweets[1].id)

        # dummy new tweets
        new_tweets2 = [
            self.create_tweet(user=self.user1)
            for i in range(22)
        ]
        new_tweets2 = new_tweets2[::-1]
        all_tweets = new_tweets2 + new_tweets + self.tweets

        # refresh to have the most recent page
        response = self.user1_client.get(
            TWEET_LIST_URL,
            {'user_id': self.user1.id,
             'created_at__gt': new_tweets[0].created_at}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 22)
        self.assertFalse(response.data['has_next_page'])
        self.assertEqual(response.data['results'][0]['id'], all_tweets[0].id)
        self.assertEqual(response.data['results'][1]['id'], all_tweets[1].id)


class TweetCacheLimitTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()

        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')

    def _paginate_to_get_tweets(self, client, user_id):
        response = client.get(TWEET_LIST_URL, {
            'user_id': user_id,
        })
        results = response.data['results']
        while response.data['has_next_page']:
            response = client.get(TWEET_LIST_URL, {
                'user_id': user_id,
                'created_at__lt': results[-1]['created_at']
            })
            results.extend(response.data['results'])
        return results

    def test_tweet_cache_limit_pagination(self):
        limit_size = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = 20

        tweets = [
            self.create_tweet(user=self.user1)
            for i in range(limit_size+page_size)
        ]
        tweets = tweets[::-1]

        # cached tweets
        cached_tweets = TweetService.load_tweets_through_cache(user_id=self.user1.id)
        self.assertEqual(len(cached_tweets), limit_size)
        db_tweets = Tweet.objects.filter(user_id=self.user1.id)
        self.assertEqual(len(db_tweets), limit_size+page_size)

        # paginate all tweets
        paginated_tweets = self._paginate_to_get_tweets(
            client=self.user2_client,
            user_id=self.user1.id,
        )
        self.assertEqual(len(paginated_tweets), limit_size+page_size)
        self.assertEqual(
            [t['id'] for t in paginated_tweets],
            [t.id for t in tweets]
        )

        # create new tweet
        new_tweet = self.create_tweet(user=self.user1)

        def _test_tweets_after_pushed_new_tweet():
            new_paginated_tweets = self._paginate_to_get_tweets(
                client=self.user2_client,
                user_id=self.user1.id,
            )
            self.assertEqual(len(new_paginated_tweets), limit_size+page_size+1)
            self.assertEqual(new_paginated_tweets[0]['id'], new_tweet.id)
            for i in range(limit_size+page_size):
                self.assertEqual(tweets[i].id, new_paginated_tweets[i+1]['id'])

        _test_tweets_after_pushed_new_tweet()

        # cache expire
        self.clear_cache()
        _test_tweets_after_pushed_new_tweet()





