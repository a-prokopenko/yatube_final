from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UserURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='leo')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_guest(self):
        urls = [
            '/auth/login/',
            '/auth/logout/',
            '/auth/signup/',
            '/auth/password_reset/',
            '/auth/password_reset/done/',
            '/auth/reset/<uidb64>/<token>/',
            '/auth/reset/done/',
        ]
        for address in urls:
            with self.subTest(address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized(self):
        urls = [
            '/auth/password_change/',
            '/auth/password_change/done/',
        ]
        for address in urls:
            with self.subTest(address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_guest_correct_template(self):
        templates_url_names = {
            '/auth/login/':
                'users/login.html',
            '/auth/signup/':
                'users/signup.html',
            '/auth/logout/':
                'users/logged_out.html',
            '/auth/password_reset/':
                'users/password_reset_form.html',
            '/auth/password_reset/done/':
                'users/password_reset_done.html',
            '/auth/reset/<uidb64>/<token>/':
                'users/password_reset_confirm.html',
            '/auth/reset/done/':
                'users/password_reset_complete.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_auth_correct_template(self):
        templates_url_names = {
            '/auth/password_change/':
                'users/password_change_form.html',
            '/auth/password_change/done/':
                'users/password_change_done.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
