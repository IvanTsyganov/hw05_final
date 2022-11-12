import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.urls import reverse
from posts.models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test group',
            slug='test_slug',
            description='test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Валидная форма создает запись в Posts"""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='forms.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        post_last = Post.objects.first()
        self.assertEqual(post_last.text, form_data['text'])
        self.assertEqual(post_last.group.id, self.group.id)
        self.assertEqual(post_last.image, f'posts/{uploaded.name}')
        self.assertEqual(post_last.author, self.post.author)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Posts"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'нОВЫЙ тестовый текст',
            'group': self.group.id,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(Post.objects.count(), post_count)
        post_last_edit = Post.objects.get(pk=self.post.id)
        self.assertEqual(post_last_edit.text, form_data['text'])
        self.assertEqual(post_last_edit.group.id, self.group.id)
        self.assertEqual(post_last_edit.author, self.post.author)

    def test_create_by_guest_post(self):
        """Валидная форма не авторизованного не создает запись в Posts"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }

        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), post_count)

    def test_create_comment_by_authorized_client(self):
        """Валидная форма авторизованного создает коммент"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
