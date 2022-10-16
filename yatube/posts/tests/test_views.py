import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..consts import LIMIT_POSTS
from ..models import Comment, Follow, Group, Post, User
from .consts import (TEST_COMMENT, TEST_DESC, TEST_IMAGE, TEST_SLUG, TEST_TEXT,
                     TEST_TITLE)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём записи в БД"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        small_gif = TEST_IMAGE
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title=TEST_TITLE,
            slug=TEST_SLUG,
            description=TEST_DESC,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEST_TEXT,
            group=cls.group,
            image=cls.image,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text=TEST_COMMENT,
        )
        cls.urls = {
            'index': reverse('posts:index'),
            'group_list': reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}),
            'profile': reverse(
                'posts:profile', kwargs={'username': cls.post.author}),
            'post_detail': reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.id}),
            'post_edit': reverse(
                'posts:post_edit', kwargs={'post_id': cls.post.id}),
            'post_create': reverse('posts:post_create'),
            'follow': reverse('posts:follow_index'),
        }
        cls.urls_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': cls.post.author}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': cls.post.id}):
                'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': cls.post.id}):
                'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:follow_index'): 'posts/follow.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаём авторизованного клиента"""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.urls_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def post_asserts(self, post, expected, image):
        self.assertEqual(post, expected)
        self.assertEqual(post.image, image)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(self.urls['index'])
        expected = Post.objects.all()[0]
        post = response.context['page_obj'][0]
        post_count = len(response.context['page_obj'])
        self.post_asserts(post, expected, self.post.image)
        self.assertEqual(post_count, 1)

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(self.urls['group_list'])
        expected = Post.objects.filter(group_id=self.post.group)[0]
        post = response.context['page_obj'][0]
        post_count = len(response.context['page_obj'])
        self.post_asserts(post, expected, self.post.image)
        self.assertEqual(post_count, 1)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(self.urls['profile'])
        expected = Post.objects.filter(author_id=self.post.author)[0]
        post = response.context['page_obj'][0]
        post_count = len(response.context['page_obj'])
        self.post_asserts(post, expected, self.post.image)
        self.assertEqual(post_count, 1)

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(self.urls['post_detail'])
        form_fields = {
            'text': forms.fields.CharField,
        }
        expected = Post.objects.filter(id=self.post.id)[0]
        post = response.context['post']
        self.post_asserts(post, expected, self.post.image)
        self.assertIsInstance(
            response.context.get('form').fields.get('text'),
            form_fields.get('text')
        )
        self.assertTrue(
            response.context.get('comments').get(text=self.comment)
        )

    def test_post_create_edit_correct_context(self):
        responses = [
            (self.authorized_client.get(self.urls['post_create'])),
            (self.authorized_client.get(self.urls['post_edit']))
        ]
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                for response in responses:
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_with_group_show_correct(self):
        response = self.authorized_client.get(self.urls['index'])
        expected = Post.objects.filter(group_id=self.post.group)[0]
        post = response.context['page_obj'][0]
        post_count = len(response.context['page_obj'])
        urls = (self.urls['index'],
                self.urls['profile'],
                self.urls['group_list'],
                )
        for url in urls:
            with self.subTest(url=url):
                self.post_asserts(post, expected, self.post.image)
                self.assertEqual(post_count, 1)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём записи в БД"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title=TEST_TITLE,
            slug=TEST_SLUG,
            description=TEST_DESC,
        )
        cls.post = Post(
            author=cls.user,
            text=TEST_TEXT,
            group=cls.group,
        )
        test_posts: list = []
        for i in range(LIMIT_POSTS + 1):
            test_posts.append(cls.post)
        Post.objects.bulk_create(test_posts)
        cls.urls = (reverse('posts:index'),
                    reverse('posts:profile',
                            kwargs={'username': cls.post.author}),
                    reverse('posts:group_list',
                            kwargs={'slug': cls.group.slug}),
                    )

    def setUp(self):
        """Создаём авторизованного клиента"""
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_paginator_first_page(self):
        """Проверяем паджинацию на первой странице"""
        for url in self.urls:
            with self.subTest(url=url):
                response_1_page = self.authorized_client.get(url)
                response_2_page = self.authorized_client.get(url + '?page=2')
                self.assertEqual(len(response_1_page.context.get('page_obj')),
                                 LIMIT_POSTS)
                self.assertEqual(
                    len(response_2_page.context.get('page_obj')), 1)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEST_TEXT,
        )
        cls.urls = {
            'index': reverse('posts:index')
        }

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index_page(self):
        first_response = self.authorized_client.get(self.urls['index'])
        self.post.delete()
        second_response = self.authorized_client.get(self.urls['index'])
        # контент первого запроса должен быть равен контенту второго
        # т.к. кэш не очищен, хотя пост удалён
        self.assertEqual(first_response.content, second_response.content)
        cache.clear()
        third_response = self.authorized_client.get(self.urls['index'])
        # контент первого запроса не должен быть равен контенту третьего
        # т.к. пост удалён и кэш очищен
        self.assertNotEqual(first_response.content, third_response.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём записи в БД"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.user_jon = User.objects.create_user(username='jon')
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
        cls.urls = {
            'follow': reverse(
                'posts:profile_follow', kwargs={'username': cls.post.author}),
            'index': reverse(
                'posts:follow_index'),
            'unfollow': reverse(
                'posts:profile_unfollow', kwargs={'username': cls.post.author})
        }

    def setUp(self):
        """Создаём авторизованного клиента"""
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.authorized_client_1.force_login(self.user_jon)
        cache.clear()

    def test_profile_follow_unfollow(self):
        # подписываемся
        self.authorized_client_1.get(self.urls['follow'])
        follow = Follow.objects.filter(
            user=self.user_jon, author=self.post.author)
        # проверяем, что бд создалась подписка
        self.assertTrue(follow.exists())
        # отписываемся
        self.authorized_client_1.get(self.urls['unfollow'])
        # проверяем, что в бд подписки нет
        self.assertFalse(follow.exists())

    def test_follow_index(self):
        # подписываемся
        self.authorized_client_1.get(self.urls['follow'])
        new_post = Post.objects.create(author=self.user, text='Новый пост')
        response_follow_user = self.authorized_client_1.get(self.urls['index'])
        # создаём нового пользователя, который не подписан на автора поста
        user_sam = User.objects.create_user(username='sam')
        self.authorized_client_2.force_login(user_sam)
        response_unfollow_user = self.authorized_client_2.get(
            self.urls['index'])
        # проверяем, что новый пост появился у подписанного пользователя
        self.assertContains(response_follow_user, new_post)
        # проверяем, что новый пост не появился у неподписанного пользователя
        self.assertNotContains(response_unfollow_user, new_post)
