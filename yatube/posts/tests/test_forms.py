import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Comment
from ..consts import TEST_IMAGE, TEST_TEXT, TEST_DESC, TEST_SLUG, TEST_TITLE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаём записи в БД"""
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.small_gif = TEST_IMAGE
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
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
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаём авторизованного клиента"""
        self.new_user = User.objects.create_user(username='jon')
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.authorized_client_1.force_login(self.user)
        self.authorized_client_2.force_login(self.new_user)

    def test_create_post_from_guest(self):
        """Гость не может создать пост"""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.guest_client.post(
            path=reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # неавторизованного пользователя перебрасывает на страницу логина
        self.assertRedirects(response,
                             ((reverse('users:login')) + '?next=%2Fcreate%2F'))
        # количество постов не изменяется
        self.assertEqual(Post.objects.count(), count_posts)

    def test_create_post_form(self):
        """Форма создания поста работает"""
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client_2.post(
            path=reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.new_user})
        )
        post = Post.objects.first()
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertEqual(post.author, self.new_user)
        self.assertEqual(post.text, form_data.get('text'))
        self.assertEqual(post.group.id, form_data.get('group'))
        self.assertEqual(post.image, f'posts/{self.uploaded}')

    def test_post_edit_form_guest(self):
        """Гость не может редактировать пост"""
        posts_count = Post.objects.count()
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание'
        )
        form_data = {
            'author': 'Гость',
            'text': 'Редактирование поста',
            'group': new_group.id
        }
        response = self.guest_client.post(
            path=reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        post = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, (reverse('users:login')
                                        + '?next=%2Fposts%2F1%2Fedit%2F'))
        # проверяем, что пост не изменился
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group.id, self.post.group.id)

    def test_post_edit_form_not_auth(self):
        """Не автор не может редактировать пост"""
        posts_count = Post.objects.count()
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание'
        )
        form_data = {
            'author': self.new_user,
            'text': 'Редактирование поста',
            'group': new_group.id
        }
        response = self.authorized_client_2.post(
            path=reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        post = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id}))
        # проверяем, что пост не изменился
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group.id, self.post.group.id)

    def test_post_edit_form(self):
        """Форма редактирования записи работает"""
        posts_count = Post.objects.count()
        new_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание'
        )
        form_data = {
            'text': 'Редактирование поста',
            'group': new_group.id
        }
        response = self.authorized_client_1.post(
            path=reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True)
        post = Post.objects.get(id=self.post.id)
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        # проверяем, что пост изменился
        self.assertEqual(post.text, form_data.get('text'))
        self.assertEqual(post.group.id, form_data.get('group'))

    def test_comment_post(self):
        """Комментарий оправляется и появляется на странице поста"""
        comment_count = Comment.objects.count()
        form_data = {'text': 'Коммент'}
        response = self.authorized_client_2.post(
            path=reverse('posts:add_comment',
                         kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_page = self.authorized_client_2.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        )
        self.assertRedirects(
            response, reverse('posts:post_detail',
                              kwargs={'post_id': self.post.id})
        )
        # количество комментариев увеличилось
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        # контент страницы содержит созданный комментарий
        self.assertContains(post_page, form_data.get('text'))

    def test_comment_post_not_auth(self):
        """Неавторизованный пользователь пытается оставить комментарий"""
        comment_count = Comment.objects.count()
        self.authorized_client_2.logout()
        form_data = {'text': 'Коммент'}
        # Неавторизованный пользователь пытается отправить форму
        response = self.authorized_client_2.post(
            path=reverse('posts:add_comment',
                         kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        post_page = self.authorized_client_2.get(
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
        # Количество комментариев не увеличилось
        self.assertEqual(Comment.objects.count(), comment_count)
