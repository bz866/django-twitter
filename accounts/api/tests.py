from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.api.views import (
    AccountViewSet,
    UserViewSet,
)
from accounts.api.serializer import (
    UserSerializer,
    SignUpSerializer,
)
from django.contrib.auth.models import User

SIGNUP_URL = "/api/accounts/signup/"


class AccountTest(TestCase):
    def setUp(self):
        client = APIClient()
        data = {
            'username': 'defaultuser',
            'password': 'defaultpassword',
            'email': 'default@email.com',
        }
        self.create_user(data)

    def create_user(self, data):
        User.objects.create_user(**data)

    def test_sign_up_one_user(self):
        user_info = {
            'username': 'adminuser',
            'password': 'adminpassword',
            'email': 'admin@email.com'
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
            'email': 'default@email.com'
        })
        self.assertEqual(response.data['message'], "Please check input")
        self.assertEqual(response.data['error']['username'], ["This username has been occupied."])
        self.assertEqual(response.status_code, 400)
        # occupied email
        response = self.client.post(SIGNUP_URL, {
            'username': 'defaultuser2',
            'password': 'defaultpassword',
            'email': 'default@email.com'
        })
        self.assertEqual(response.data['message'], "Please check input")
        self.assertEqual(response.data['error']['email'], ["This email has been occupied."])
        self.assertEqual(response.status_code, 400)

    def test_signup_username_email_case_insensitive(self):
        # defaultuser is registered
        response = self.client.post(SIGNUP_URL, {
            'username': 'DEFAULTUSER',
            'password': 'defaultpassword',
            'email': 'default@email.com'
        })
        self.assertEqual(response.data['message'], "Please check input")
        self.assertEqual(response.data['error']['username'], ["This username has been occupied."])
        self.assertEqual(response.status_code, 400)
        # default@email.com is registered
        response = self.client.post(SIGNUP_URL, {
            'username': 'defaultuser',
            'password': 'defaultpassword',
            'email': 'DEFAULT@emAil.COM'
        })
        self.assertEqual(response.data['message'], "Please check input")
        self.assertEqual(response.data['error']['username'], ["This username has been occupied."])
        self.assertEqual(response.status_code, 400)

    def test_login(self):
        pass

    def test_logout(self):
        pass

    def test_login_status(self):
        pass

