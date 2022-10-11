from http import HTTPStatus

from django.test import Client, TestCase
from django.core.cache import cache

from ..models import Group, Post, User


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            pk='1',
        )
        cls.posts_urls = {
            '/': 'all',
            f'/group/{cls.group.slug}/': 'all',
            f'/profile/{cls.post.author}/': 'all',
            f'/posts/{cls.post.pk}/': 'all',
            f'/posts/{cls.post.pk}/edit/': 'author',
            '/create/': 'authorized',
            '/follow/': 'authorized',
        }
        cls.posts_urls_templates = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
            '/follow/': 'posts/follow.html',
        }

    def setUp(self):
        new_user = User.objects.create_user(username='jon')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.authorized_client.force_login(new_user)
        cache.clear()

    def test_urls_guest(self):
        for address, access in self.posts_urls.items():
            if access == 'all':
                with self.subTest(address=address):
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
            elif access == 'authorized':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
            elif access == 'author':
                with self.subTest(address=address):
                    response = self.author_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        for address, template in self.posts_urls_templates.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_404(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
