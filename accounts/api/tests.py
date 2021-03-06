from rest_framework.test import APIClient
from testing.testcases import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

SIGNUP_URL = "/api/accounts/signup/"
LOGIN_URL = "/api/accounts/login/"
LOGIN_STATUS_URL = "/api/accounts/login_status/"
LOGOUT_URL = "/api/accounts/logout/"


class AccountTest(TestCase):
    def setUp(self):
        self.clear_cache()
        self.client = APIClient()
        default_user_data = {
            'username': 'defaultuser',
            'password': 'defaultpassword',
            'email': 'defaultuser@email.com',
        }
        user = self.create_user(**default_user_data)

    def test_sign_up_one_user(self):
        user_info = {
            'username': 'adminuser',
            'password': 'adminpassword',
            'email': 'adminuser@email.com'
        }
        # test sign up url, no GET method
        response = self.client.get(SIGNUP_URL, user_info)
        self.assertEqual(response.status_code, 405)

        # sign up a normal user
        response = self.client.post(SIGNUP_URL, data=user_info)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.count(), 2) # new + defaultsuser
        self.assertEqual(response.data['user']['username'], user_info['username'])
        self.assertEqual(response.data['user']['email'], user_info['email'])

    def test_sign_up_invalid_input(self):
        # too long or too short username or password
        ## too short username
        response = self.client.post(SIGNUP_URL, data={
            'username': 'admin',
            'password': 'adminpassword',
            'email': 'adminx@email.com'
        })
        self.assertEqual(response.status_code, 400)
        response = self.client.post(SIGNUP_URL, data={
            'username': 'adminlong',
            'password': 'admin',
            'email': 'adminx@email.com'
        })
        self.assertEqual(response.status_code, 400)
        response = self.client.post(SIGNUP_URL, data={
            'username': 'adminlong',
            'password': 'admin',
            'email': 'adminx@@email.com'
        })
        self.assertEqual(response.status_code, 400)

    def test_duplicated_username_or_email(self):
        # occupied username
        response = self.client.post(SIGNUP_URL, {
            'username': 'defaultuser',
            'password': 'defaultpassword',
            'email': 'defaultuser@email.com'
        })
        self.assertEqual(response.data['message'], "Please check input")
        self.assertEqual(response.data['error']['username'], ["This username has been occupied."])
        self.assertEqual(response.status_code, 400)
        # occupied email
        response = self.client.post(SIGNUP_URL, {
            'username': 'defaultuser2',
            'password': 'defaultpassword',
            'email': 'defaultuser@email.com'
        })
        self.assertEqual(response.data['message'], "Please check input")
        self.assertEqual(response.data['error']['email'], ["This email has been occupied."])
        self.assertEqual(response.status_code, 400)

    def test_signup_username_email_case_insensitive(self):
        # defaultuser is registered
        response = self.client.post(SIGNUP_URL, {
            'username': 'DEFAULTUSER',
            'password': 'defaultpassword',
            'email': 'defaultuser@email.com'
        })
        self.assertEqual(response.data['message'], "Please check input")
        self.assertEqual(response.data['error']['username'], ["This username has been occupied."])
        self.assertEqual(response.status_code, 400)
        # default@email.com is registered
        response = self.client.post(SIGNUP_URL, {
            'username': 'defaultuser',
            'password': 'defaultpassword',
            'email': 'DEFAULTUSER@emAil.COM'
        })
        self.assertEqual(response.data['message'], "Please check input")
        self.assertEqual(response.data['error']['username'], ["This username has been occupied."])
        self.assertEqual(response.status_code, 400)

    def test_login(self):
        # GET method not allowed
        response = self.client.get(LOGIN_URL, {
            'username': 'defaultuser',
            'password': 'defaultpassword',
        })
        self.assertEqual(response.status_code, 405)
        response = self.client.post(LOGIN_URL, {
            'username': 'defaultuser',
            'password': 'defaultpassword',
        })
        self.assertEqual(response.status_code, 200)

        # username case-insensitive
        response = self.client.post(LOGIN_URL, {
            'username': 'DEFAULTUSER',
            'password': 'defaultpassword',
        })
        self.assertEqual(response.status_code, 200)

        # username not exist
        response = self.client.post(LOGIN_URL, {
            'username': 'userfromnowhere',
            'password': 'passwordfromnowhere',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['username'], ["User name not exist"])

        # username and password not match
        response = self.client.post(LOGIN_URL, {
            'username': 'defaultuser',
            'password': 'wrong password',
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], "Username and password not match")

    def test_logout(self):
        # GET method not allowed
        response = self.client.get(LOGOUT_URL)
        self.assertEqual(response.status_code, 405)

        # All following user-specified status check are not finished
        # client can only save the most recent user information
        # it needs extra logic in Login to realize the multiple clients function
        response = self.client.post(LOGIN_URL, {
            'username': 'defaultuser',
            'password': 'defaultpassword',
        })
        response = self.client.get(LOGIN_STATUS_URL, {'username': 'defaultuser'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['has_logged_in'], True)
        self.assertEqual(response.data['user']['username'], 'defaultuser')

        self.client.post(SIGNUP_URL, {
            'username': 'seconduser',
            'password': 'secondpassword',
            'email': 'seconduser@email.com',
        })
        self.assertEqual(User.objects.count(), 2)
        response = self.client.get(LOGIN_STATUS_URL, {'username': 'seconduser'})
        self.assertEqual(response.data['has_logged_in'], True)
        self.assertEqual(response.data['user']['username'], 'seconduser')

        # two users logged in
        response = self.client.get(LOGIN_STATUS_URL, {'username': 'defaultuser'}) # not really got the status of the default user
        self.assertEqual(response.data['has_logged_in'], True) # just used the only status(seconduser) as the True
        response = self.client.get(LOGIN_STATUS_URL, {'username': 'seconduser'})
        self.assertEqual(response.data['has_logged_in'], True)

        # username case-insensitive
        # logout defaultuser
        response = self.client.post(LOGOUT_URL, {'username': 'DEFAULTUSER'})
        self.assertEqual(response.status_code, 200)
        response = self.client.get(LOGIN_STATUS_URL, {'username': 'defaultuser'})
        self.assertEqual(response.data['has_logged_in'], False)
        # second user should still online on the serverside
        # but the client only save the status of the most recent user
        # need to access the server to get the status of seconduser
        response = self.client.get(LOGIN_STATUS_URL, {'username': 'seconduser'})
        self.assertEqual(response.data['has_logged_in'], False)

    def test_login_status(self):
        response = self.client.post(LOGIN_URL, {
            'username': 'defaultuser',
            'password': 'defaultpassword',
        })
        # POST method not allowed
        response = self.client.post(LOGIN_STATUS_URL)
        self.assertEqual(response.status_code, 405)
        response = self.client.get(LOGIN_STATUS_URL)
        self.assertEqual(response.status_code, 200)


class UserProfileTest(TestCase):
    def setUp(self) -> None:
        self.user1 = self.create_user(username='user1')
        self.user1_client = APIClient()
        self.user1_client.force_authenticate(user=self.user1)
        self.user2 = self.create_user(username='user2')
        self.user2_client = APIClient()
        self.user2_client.force_authenticate(user=self.user2)

    def test_update(self):
        # user1 create profile
        profile = self.user1.profile
        url_profile_update = '/api/userprofiles/{}/'.format(profile.id)
        data = {
            'nickname': 'newnickname',
            'avatar': SimpleUploadedFile(
                name='my-avatar.jpg',
                content=str.encode('a fake image'),
                content_type='image/jpeg',
            ),
        }
        # PUT method only
        response = self.user1_client.post(url_profile_update, data)
        self.assertEqual(response.status_code, 405)
        # non-anonymous client
        response = self.anonymous_client.put(url_profile_update, data)
        self.assertEqual(response.status_code, 403)
        # missing update content
        response = self.user1_client.put(url_profile_update)
        self.assertEqual(response.status_code, 200)
        # only allow update owned profile
        response = self.user2_client.put(url_profile_update, data)
        self.assertEqual(response.status_code, 403)
        # access non-exist profile
        response = self.user1_client.put('/api/userprofiles/-1/', data)
        self.assertEqual(response.status_code, 404)

        # update the profile
        # response = self.user1_client.put(url_profile_update, data)
        response = self.user1_client.put(url_profile_update, {
            'nickname': 'newnickname',
            'avatar': SimpleUploadedFile(
                name='my-avatar.jpg',
                content=str.encode('a fake image'),
                content_type='image/jpeg',
            )
        })
        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.nickname, 'newnickname')
        self.assertTrue('my-avatar' in response.data['avatar'])
        self.assertIsNotNone(profile.avatar)

        # only update nickname
        response = self.user1_client.put(url_profile_update, {'nickname': 'another nickname'})
        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.nickname, 'another nickname')
        self.assertTrue('my-avatar' in response.data['avatar'])
        self.assertIsNotNone(profile.avatar)







