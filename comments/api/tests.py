from comments.models import Comment
from django.utils import timezone
from rest_framework.test import APIClient
from testing.testcases import TestCase
from tweets.models import Tweet
import time
import datetime

CREATE_URL = '/api/comments/'
DETAIL_URL = '/api/comments/{}/'


class CommentTest(TestCase):

    def setUp(self) -> None:
        # dummy user
        self.user1_client = APIClient()
        self.user1 = self.create_user(username='user1')
        self.user1_client.force_authenticate(user=self.user1)
        self.user2_client = APIClient()
        self.user2 = self.create_user(username='user2')
        self.user2_client.force_authenticate(user=self.user2)
        # dummy tweet
        self.tweet1 = Tweet.objects.create(
            user=self.user1,
            content='tweet 1 for comment test'
        )
        self.tweet2 = Tweet.objects.create(
            user=self.user2,
            content='tweet without any comments'
        )

    def test_create(self):
        # POST method only
        response = self.user1_client.get(CREATE_URL, {'tweet_id': self.tweet1.id, 'content': 'sample comment'})
        self.assertEqual(response.status_code, 405)
        # non-anonymous user
        response = self.anonymous_client.post(CREATE_URL, {'tweet_id': self.tweet1.id, 'content': 'sample comment'})
        self.assertEqual(response.status_code, 403)
        # only tweet_id
        response = self.user1_client.post(CREATE_URL, {'tweet_id': self.tweet1.id})
        self.assertEqual(response.status_code, 400)
        # only content
        response = self.user1_client.post(CREATE_URL, {'content': 'sample comment'})
        self.assertEqual(response.status_code, 400)
        # too long content
        response = self.user1_client.post(CREATE_URL, {
            'tweet_id': self.tweet1.id,
            'content': 'x'*141,
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "Invalid Comment Input")
        # too short content
        response = self.user1_client.post(CREATE_URL, {
            'tweet_id': self.tweet1.id,
            'content': '', # at least 1 character
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "Invalid Comment Input")
        # no tweet exists
        response = self.user1_client.post(CREATE_URL, {'tweet_id': 9999, 'content': 'sample comment'})
        self.assertEqual(response.status_code, 400)

        # valid comment creation
        response = self.user1_client.post(CREATE_URL, {'tweet_id': self.tweet1.id, 'content': 'sample comment'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(response.data['tweet_id'], self.tweet1.id)
        self.assertEqual(response.data['content'], 'sample comment')

    def test_update(self):
        # dummy comment
        comment = Comment.objects.create(
            user=self.user1,
            tweet=self.tweet1,
            content='original comment'
        )
        UPDATE_URL = DETAIL_URL.format(comment.id)

        # PUT method only
        response = self.user1_client.get(UPDATE_URL, {'content': 'updated content'})
        self.assertEqual(response.status_code, 405)
        # non-anonymous user
        response = self.anonymous_client.put(UPDATE_URL, {'content': 'updated content'})
        self.assertEqual(response.status_code, 403)
        # comment doesn't exist
        response = self.user1_client.put(DETAIL_URL.format(999), {'content': 'updated content'})
        self.assertEqual(response.status_code, 404)
        # user doesn't own the comment
        response = self.user2_client.put(UPDATE_URL, {'content': 'updated content'})
        self.assertEqual(response.status_code, 403)
        # user can only update the content
        # the module will ignore changes that are not content
        before_create_time = comment.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        before_update_time = comment.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        print("CREATE: ", before_create_time)
        print("UPDATE: ", before_update_time)
        now = time.time()
        response = self.user1_client.put(UPDATE_URL, {
            'content': 'updated content',
            'user_id': self.user2.id, # silent mode for non-content change
            'tweet_id': self.tweet2.id, # silent mode for non-content change
            'created_at': timezone.now(),
        })
        self.assertEqual(response.status_code, 200)
        comment.refresh_from_db() # re-load updated data from the database
        self.assertEqual(response.data['content'], 'updated content')
        self.assertEqual(response.data['user']['id'], self.user1.id)
        self.assertEqual(response.data['tweet_id'], self.tweet1.id)
        self.assertEqual(response.data['created_at'], before_create_time)
        self.assertNotEqual(response.data['created_at'], timezone.now())
        self.assertNotEqual(response.data['updated_at'], before_update_time) # TODO updated_at before and after should not be the same
        self.assertNotEqual(response.data['updated_at'], timezone.now())

    def test_destroy(self):# dummy comment
        comment = Comment.objects.create(
            user=self.user1,
            tweet=self.tweet1,
            content='original comment'
        )
        DELETE_URL = DETAIL_URL.format(comment.id)
        # DELETE method only
        response = self.user1_client.post(DELETE_URL)
        self.assertEqual(response.status_code, 405)
        # non-anonymous client
        response = self.anonymous_client.delete(DELETE_URL)
        self.assertEqual(response.status_code, 403)
        # user doesn't own the comment
        response = self.user2_client.delete(DELETE_URL)
        self.assertEqual(response.status_code, 403)
        # non exist comment
        response = self.user1_client.delete(DETAIL_URL.format(999))
        self.assertEqual(response.status_code, 404)

        # delete
        cnt_comments_before_delete = Comment.objects.count()
        response = self.user1_client.delete(DELETE_URL)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Comment.objects.count(), cnt_comments_before_delete-1)

