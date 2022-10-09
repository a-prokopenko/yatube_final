import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()
POST_COUNT: int = 13
FIRST_PAGE_COUNT: int = 10
SECOND_PAGE_COUNT: int = 3
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём записи в БД"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.image,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаём авторизованного клиента"""
        user = self.user
        self.authorized_client = Client()
        self.authorized_client.force_login(user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.post.author}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.id}
                    ): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        expected = list(Post.objects.all())
        post = response.context.get('page_obj')
        self.assertEqual(
            post.object_list, expected
        )
        self.assertEqual(
            post[0].image, self.post.image
        )

    def test_group_list_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        expected = list(Post.objects.filter(group_id=self.group.id))
        post = response.context.get('page_obj')
        self.assertEqual(
            post.object_list, expected
        )
        self.assertEqual(
            post[0].image, self.post.image
        )

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        expected = list(Post.objects.filter(author_id=self.post.author))
        post = response.context.get('page_obj')
        self.assertEqual(
            post.object_list, expected
        )
        self.assertEqual(
            post[0].image, self.post.image
        )

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
        }
        expected = Post.objects.filter(id=self.post.id)[0]
        post = response.context.get('post')
        self.assertEqual(
            response.context.get('post'), expected
        )
        self.assertEqual(
            post.image, self.post.image
        )
        self.assertIsInstance(
            response.context.get('form').fields.get('text'),
            form_fields.get('text')
        )
        self.assertTrue(
            response.context.get('comments').get(text=self.comment)
        )

    def test_post_create_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_with_group_show_correct(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context.get('page_obj')[0]
        urls = (reverse('posts:index'),
                reverse('posts:profile',
                        kwargs={'username': self.post.author}),
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug}),
                )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group, self.post.group)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём записи в БД"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        test_posts: list = []
        for i in range(POST_COUNT):
            test_posts.append(cls.post)
        Post.objects.bulk_create(test_posts)

    def setUp(self):
        """Создаём авторизованного клиента"""
        user = self.user
        self.authorized_client = Client()
        self.authorized_client.force_login(user)
        cache.clear()

    def test_paginator_first_page(self):
        """Проверяем паджинацию на первой странице"""
        urls = (reverse('posts:index'),
                reverse('posts:profile',
                        kwargs={'username': self.post.author}),
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug}),
                )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context.get('page_obj')), FIRST_PAGE_COUNT
                )

    def test_paginator_second_page(self):
        """Проверяем паджинацию на второй странице"""
        urls = (reverse('posts:index'),
                reverse('posts:profile',
                        kwargs={'username': self.post.author}),
                reverse('posts:group_list',
                        kwargs={'slug': self.group.slug}),
                )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url + '?page=2')
                self.assertEqual(
                    len(response.context.get('page_obj')), SECOND_PAGE_COUNT)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        user = self.user
        self.authorized_client = Client()
        self.authorized_client.force_login(user)

    def test_cache_index_page(self):
        first_response = self.authorized_client.get(reverse('posts:index'))
        self.post.delete()
        second_response = self.authorized_client.get(reverse('posts:index'))
        # контент первого запроса должен быть равен контенту второго
        # т.к. кэш не очищен, хотя пост удалён
        self.assertEqual(first_response.content, second_response.content)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        # контент первого запроса не должен быть равен контенту третьего
        # т.к. пост удалён и кэш очищен
        self.assertNotEqual(first_response.content, third_response.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём записи в БД"""
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
        )

    def setUp(self):
        """Создаём авторизованного клиента"""
        self.user_jon = User.objects.create_user(username='jon')
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.authorized_client_1.force_login(self.user_jon)
        cache.clear()

    def test_profile_follow_unfollow(self):
        # подписываемся
        self.authorized_client_1.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.post.author}))
        follow = Follow.objects.filter(
            user=self.user_jon, author=self.post.author)
        # проверяем, что бд создалась подписка
        self.assertTrue(follow.exists())
        # отписываемся
        self.authorized_client_1.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.post.author}))
        # проверяем, что в бд подписки нет
        self.assertFalse(follow.exists())

    def test_follow_index(self):
        # подписываемся
        self.authorized_client_1.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user}))
        new_post = Post.objects.create(author=self.user, text='Новый пост')
        response_follow_user = self.authorized_client_1.get(
            reverse('posts:follow_index'))
        # создаём нового пользователя, который не подписан на автора поста
        user_sam = User.objects.create_user(username='sam')
        self.authorized_client_2.force_login(user_sam)
        response_unfollow_user = self.authorized_client_2.get(
            reverse('posts:follow_index'))
        # проверяем, что новый пост появился у подписанного пользователя
        self.assertContains(response_follow_user, new_post)
        # проверяем, что новый пост не появился у неподписанного пользователя
        self.assertNotContains(response_unfollow_user, new_post)
