import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём записи в БД"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
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

    def test_create_post_form_test(self):
        """Валидная форма создаёт запись"""
        new_user = User.objects.create_user(username='jon')
        self.authorized_client.force_login(new_user)
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            path=reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(id=2)
        self.assertRedirects(
            response, reverse('posts:profile',
                              kwargs={'username': new_user})
        )
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertEqual(post.text, form_data.get('text'))
        self.assertEqual(post.author, new_user)
        self.assertEqual(post.group.id, form_data.get('group'))
        self.assertEqual(post.image, f'posts/{self.uploaded}')

    def test_post_edit_form_test(self):
        """Форма редактирования записи работает"""
        posts_count = Post.objects.count()
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание'
        )
        form_data = {
            'author': self.post.author,
            'text': 'Редактирование поста',
            'group': new_group.id
        }
        response = self.authorized_client.post(
            path=reverse('posts:post_edit',
                         kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_edit = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post_edit.text, form_data.get('text'))
        self.assertEqual(post_edit.group.id, form_data.get('group'))

    def test_comment_post(self):
        """Комментарий оправляется и появляется на странице поста"""
        form_data = {'text': 'Коммент'}
        response = self.authorized_client.post(
            path=reverse('posts:add_comment',
                         kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_page = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id})
        )
        self.assertContains(post_page, form_data.get('text'))

    def test_comment_post_not_auth(self):
        """Неавторизованный пользователь пытается оставить комментарий"""
        self.authorized_client.logout()
        form_data = {'text': 'Коммент'}
        # Неавторизованный пользователь пытается отправить форму
        response = self.authorized_client.post(
            path=reverse('posts:add_comment',
                         kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_page = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        )
        # Неавторизованный пользователь редиректится на страницу логина
        self.assertRedirects(
            response, ((reverse('users:login'))
                       + f'?next=/posts/{self.post.id}/comment/')
        )
        # Комментарий от неавторизованного пользователя не появляется
        self.assertNotContains(post_page, form_data.get('text'))
