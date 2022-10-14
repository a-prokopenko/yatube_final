from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..consts import TEST_DESC, TEST_SLUG, TEST_TEXT, TEST_TITLE
from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title=TEST_TITLE,
            slug=TEST_SLUG,
            description=TEST_DESC,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEST_TEXT,
            group=cls.group,
        )
        cls.posts_urls = {
            '/': 'all',
            f'/group/{cls.group.slug}/': 'all',
            f'/profile/{cls.post.author}/': 'all',
            f'/posts/{cls.post.id}/': 'all',
            f'/posts/{cls.post.id}/edit/': 'author',
            '/create/': 'authorized',
            '/follow/': 'authorized',
        }
        cls.posts_urls_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': cls.post.author}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': cls.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': cls.post.id}
                    ): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }

    def setUp(self):
        self.new_user = User.objects.create_user(username='jon')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.authorized_client.force_login(self.new_user)
        cache.clear()

    def test_urls_guest(self):
        for address, access in self.posts_urls.items():
            if access == 'all':
                with self.subTest(address=address):
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized(self):
        for address, access in self.posts_urls.items():
            if access == 'authorized':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_author(self):
        for address, access in self.posts_urls.items():
            if access == 'author':
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
