from django.conf import settings
from friendships.models import Friendship
from newsfeeds.models import NewsFeed
from newsfeeds.services import NewsFeedService
from testing.testcases import TestCase

LIST_NEWSFEED_URL = '/api/newsfeeds/'
POST_TWEET_URL = '/api/tweets/'


class NewsFeedTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        
        # dummy users
        self.user1, self.user1_client = self.create_user_and_client(
            username='username1'
        )
        self.user2, self.user2_client = self.create_user_and_client(
            username='username2'
        )
        self.user3, self.user3_client = self.create_user_and_client(
            username='username3'
        )

        # dummy friendships
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        Friendship.objects.create(from_user=self.user2, to_user=self.user1)
        Friendship.objects.create(from_user=self.user3, to_user=self.user1)

    def test_list(self):
        # post tweet
        for i in range(2):
            response = self.user2_client.post(POST_TWEET_URL, {
                'content': "user2 #{} posting. This tweet should be fanout to my followers".format(
                    i)
            })
            self.assertEqual(response.status_code, 201)
        for i in range(1):
            response = self.user1_client.post(POST_TWEET_URL, {
                'content': "user1 #{} posting. This tweet should be fanout to my followers".format(
                    i)
            })
            self.assertEqual(response.status_code, 201)

        # must login
        response = self.anonymous_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.status_code, 403)
        # only allow GET method
        response = self.user2_client.post(LIST_NEWSFEED_URL)
        self.assertEqual(response.status_code, 405)

        # can see own tweets
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        # fanout to right followers
        response = self.user1_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        response = self.user3_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(len(response.data['results']), 1)

        # newsfeed order by created_at in descending order
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['results'][0]['tweet']['user']['username'], 'username1')
        self.assertEqual(response.data['results'][1]['tweet']['user']['username'], 'username2')
        self.assertEqual(response.data['results'][2]['tweet']['user']['username'], 'username2')
        response = self.user1_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['results'][0]['tweet']['user']['username'], 'username1')
        self.assertEqual(response.data['results'][1]['tweet']['user']['username'], 'username2')
        self.assertEqual(response.data['results'][2]['tweet']['user']['username'], 'username2')

    def test_like_tweet_and_comment(self):
        # create tweet
        tweet1 = self.create_tweet(user=self.user1)
        tweet2 = self.create_tweet(user=self.user2)
        tweet3 = self.create_tweet(user=self.user3)
        NewsFeedService().fanout_to_followers(tweet1)
        NewsFeedService().fanout_to_followers(tweet2)
        NewsFeedService().fanout_to_followers(tweet3)
        # create comment
        comment1 = self.create_comment(user=self.user1, tweet=tweet1)
        comment2 = self.create_comment(user=self.user3, tweet=tweet1)
        # create like
        self.create_like(user=self.user3, object=tweet1)
        self.create_like(user=self.user2, object=tweet1)
        self.create_like(user=self.user2, object=comment1)
        self.create_like(user=self.user3, object=comment1)

        # check tweet like
        response = self.user1_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['results'][0]['tweet']['id'], tweet2.id)
        self.assertEqual(response.data['results'][0]['tweet']['comment_count'], 0)
        self.assertEqual(response.data['results'][0]['tweet']['has_liked'], False)
        self.assertEqual(response.data['results'][0]['tweet']['like_count'], 0)
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['results'][1]['tweet']['id'], tweet1.id)
        self.assertEqual(response.data['results'][1]['tweet']['comment_count'], 2)
        self.assertEqual(response.data['results'][1]['tweet']['has_liked'], True)
        self.assertEqual(response.data['results'][1]['tweet']['like_count'], 2)
        response = self.user3_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.data['results'][0]['tweet']['id'], tweet3.id)
        self.assertEqual(response.data['results'][0]['tweet']['comment_count'], 0)
        self.assertEqual(response.data['results'][0]['tweet']['has_liked'], False)
        self.assertEqual(response.data['results'][0]['tweet']['like_count'], 0)
        self.assertEqual(response.data['results'][1]['tweet']['id'], tweet1.id)
        self.assertEqual(response.data['results'][1]['tweet']['comment_count'], 2)
        self.assertEqual(response.data['results'][1]['tweet']['has_liked'], True)
        self.assertEqual(response.data['results'][1]['tweet']['like_count'], 2)


class NewsFeedPagination(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')
        self.user3, self.user3_client = self.create_user_and_client(username='user3')
        # dummy friendship
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        Friendship.objects.create(from_user=self.user2, to_user=self.user1)
        Friendship.objects.create(from_user=self.user3, to_user=self.user1)
        Friendship.objects.create(from_user=self.user2, to_user=self.user3)
        #          user1
        #       /*       *\\
        #     /            \\*
        #     user3   *--  user2

    def test_newsfeeds_endless_pagination(self):
        self.user1_tweets_data = [
            self.user1_client.post(POST_TWEET_URL, {
                'content': 'default content'
            }).data['tweet']
            for i in range(41)
        ]
        self.user1_tweets_data = self.user1_tweets_data[::-1]
        # check endless pagination loading
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 20)
        self.assertTrue(response.data['has_next_page'])
        # newsfeed order by created at in descending
        self.assertEqual(
            response.data['results'][0]['tweet']['id'],
            self.user1_tweets_data[0]['id']
        )
        self.assertEqual(
            response.data['results'][1]['tweet']['id'],
            self.user1_tweets_data[1]['id']
        )
        # load next page
        response = self.user2_client.get(LIST_NEWSFEED_URL, {
            'created_at__lt': response.data['results'][-1]['tweet']['created_at']
        })
        self.assertEqual(len(response.data['results']), 20)
        self.assertTrue(response.data['has_next_page'])
        self.assertEqual(
            response.data['results'][0]['tweet']['id'],
            self.user1_tweets_data[20]['id']
        )
        self.assertEqual(
            response.data['results'][1]['tweet']['id'],
            self.user1_tweets_data[21]['id']
        )
        # load bottom page
        response = self.user2_client.get(LIST_NEWSFEED_URL, {
            'created_at__lt': response.data['results'][-1]['tweet']['created_at']
        })
        self.assertEqual(len(response.data['results']), 1)
        self.assertFalse(response.data['has_next_page'])
        self.assertEqual(
            response.data['results'][0]['tweet']['id'],
            self.user1_tweets_data[40]['id']
        )

        # dummy new post
        self.user3_tweets_data = [
            self.user3_client.post(POST_TWEET_URL, {
                'content': 'default content'
            }).data['tweet']
            for i in range(10)
        ]
        self.user3_tweets_data = self.user3_tweets_data[::-1]
        all_tweets_data = self.user3_tweets_data + self.user1_tweets_data
        # refresh for new posts
        response = self.user2_client.get(LIST_NEWSFEED_URL, {
            'created_at__gt': self.user1_tweets_data[0]['created_at']
        })
        # newsfeeds created after the tweet
        # 10 + 1(self.user1_tweets_data[0] tweet's newsfeed created after tweet if self)
        self.assertEqual(len(response.data['results']), 11)
        self.assertFalse(response.data['has_next_page'])
        self.assertEqual(
            response.data['results'][0]['tweet']['id'],
            self.user3_tweets_data[0]['id']
        )
        self.assertEqual(
            response.data['results'][10]['tweet']['id'],
            self.user1_tweets_data[0]['id']
        )
        self.assertEqual(
            response.data['results'][-1]['tweet']['id'],
            self.user1_tweets_data[0]['id']
        )


class NewsFeedCacheTest(TestCase):

    def setUp(self):
        self.clear_cache()
        
        self.user1, self.user1_client = self.create_user_and_client(username='user1')
        self.user2, self.user2_client = self.create_user_and_client(username='user2')

        # create followings and followers for user2
        for i in range(2):
            follower = self.create_user('user1_follower{}'.format(i))
            Friendship.objects.create(from_user=follower, to_user=self.user1)
        for i in range(3):
            following = self.create_user('user2_following{}'.format(i))
            Friendship.objects.create(from_user=self.user2, to_user=following)

    def test_user_cache(self):
        profile = self.user2.profile
        profile.nickname = 'user2_new_nickname'
        profile.save()

        self.assertEqual(self.user1.username, 'user1')
        self.create_newsfeed(self.user2, self.create_tweet(self.user1))
        self.create_newsfeed(self.user2, self.create_tweet(self.user2))

        response = self.user2_client.get(LIST_NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user2')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'user2_new_nickname')
        self.assertEqual(results[1]['tweet']['user']['username'], 'user1')

        self.user1.username = 'user1'
        self.user1.save()
        profile.nickname = 'user1_new_nickname'
        profile.save()

        response = self.user2_client.get(LIST_NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user2')
        self.assertEqual(results[0]['tweet']['user']['nickname'], 'user1_new_nickname')
        self.assertEqual(results[1]['tweet']['user']['username'], 'user1')

    def test_tweet_cache(self):
        tweet = self.create_tweet(self.user1, 'content1')
        self.create_newsfeed(self.user2, tweet)
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user1')
        self.assertEqual(results[0]['tweet']['content'], 'content1')

        # update username
        self.user1.username = 'user1'
        self.user1.save()
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['user']['username'], 'user1')

        # update content
        tweet.content = 'content2'
        tweet.save()
        response = self.user2_client.get(LIST_NEWSFEED_URL)
        results = response.data['results']
        self.assertEqual(results[0]['tweet']['content'], 'content2')


class NewsFeedCacheLimitTest(TestCase):

    def setUp(self) -> None:
        self.clear_cache()
        
        self.user1, self.user1_client = self.create_user_and_client(
            username='user1')
        self.user2, self.user2_client = self.create_user_and_client(
            username='user2')
        self.user3, self.user3_client = self.create_user_and_client(
            username='user3')
        # dummy friendship
        Friendship.objects.create(from_user=self.user1, to_user=self.user2)
        Friendship.objects.create(from_user=self.user2, to_user=self.user1)
        Friendship.objects.create(from_user=self.user3, to_user=self.user1)
        Friendship.objects.create(from_user=self.user2, to_user=self.user3)
        #          user1
        #       /*       *\\
        #     /            \\*
        #     user3   *--  user2

    def _next_page_data(self, client, timestamp):
        response = client.get(LIST_NEWSFEED_URL, {
            'created_at__lt': timestamp,
        })
        return response.data

    def _refresh_data(self, client, timestamp):
        response = client.get(LIST_NEWSFEED_URL, {
            'created_at__gt': timestamp,
        })
        return response.data

    def _paginate_to_get_newsfeeds(self, client):
        response = client.get(LIST_NEWSFEED_URL)
        newsfeeds = response.data['results']
        while response.data['has_next_page']:
            response = client.get(LIST_NEWSFEED_URL, {
                'created_at__lt': response.data['results'][-1]['created_at']
            })
            newsfeeds.extend(response.data['results'])
        return newsfeeds

    def test_newsfeed_cache_limit_pagination(self):
        limit_size = settings.REDIS_LIST_LENGTH_LIMIT
        page_size = 20
        users = [
            self.create_user(username='dummyuser{}'.format(i))
            for i in range(5)
        ]
        newsfeeds = []
        for i in range(limit_size + page_size):
            tweet = self.create_tweet(user=users[i % 5])
            feed = self.create_newsfeed(user=self.user2, tweet=tweet)
            newsfeeds.append(feed)
        newsfeeds = newsfeeds[::-1]

        # newsfeed inside and outside cache
        cached_newsfeeds = NewsFeedService.load_newsfeeds_through_cache(
            user_id=self.user2.id
        )
        self.assertEqual(len(cached_newsfeeds), limit_size)
        db_newsfeeds = NewsFeed.objects.filter(user=self.user2)
        self.assertEqual(len(db_newsfeeds), limit_size+page_size)

        paginated_newsfeeds = self._paginate_to_get_newsfeeds(
            client=self.user2_client
        )
        self.assertEqual(len(paginated_newsfeeds), limit_size+page_size)
        self.assertEqual(
            [f['id'] for f in paginated_newsfeeds],
            [f.id for f in newsfeeds]
        )

        # new posts fanout to followers' newsfeeds
        celebrity, celebrity_client = self.create_user_and_client(
            username='celebrity'
        )
        self.create_friendship(from_user=self.user2, to_user=celebrity)
        tweet_celebrity = self.create_tweet(user=celebrity)
        NewsFeedService.fanout_to_followers(tweet_celebrity)

        def _test_newsfeeds_after_new_feed_pushed():
            db_newsfeeds = NewsFeed.objects.filter(user=self.user2)
            self.assertEqual(len(db_newsfeeds), limit_size+page_size+1)
            new_paginated_newsfeed = self._paginate_to_get_newsfeeds(
                client=self.user2_client
            )
            self.assertEqual(
                new_paginated_newsfeed[0]['tweet']['id'],
                tweet_celebrity.id
            )
            for i in range(limit_size+page_size):
                self.assertEqual(
                    new_paginated_newsfeed[i+1]['id'],
                    newsfeeds[i].id
                )

        _test_newsfeeds_after_new_feed_pushed()

        # keys expire
        self.clear_cache()
        _test_newsfeeds_after_new_feed_pushed()





        