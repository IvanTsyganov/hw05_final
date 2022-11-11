import shutil
import tempfile
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django import forms

from posts.models import Post, Group, Comment, Follow

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostViewTemplatesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_t = User.objects.create_user(username='auth')
        cls.group_t = Group.objects.create(
            title='test group',
            slug='test_slug',
            description='test description',
        )
        cls.post_t = Post.objects.create(
            author=cls.user_t,
            text='Тестовый пост',
            group=cls.group_t,
        )

    def setUp(self):
        cache.clear()
        self.user_author = PostViewTemplatesTests.user_t
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user_author)

    def test_pages_uses_correct_template(self):
        """"URL использует нужный шаблон"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': self.group_t.slug}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user_t.username}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_t.id}): (
                'posts/post_detail.html'),
            reverse('posts:post_edit', kwargs={'post_id': self.post_t.id}): (
                'posts/post_create.html'),
            reverse('posts:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PaginatorViewsTest(TestCase):

    POST_COUNT = 15

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_p = User.objects.create_user(username='auth2')
        cls.group_p = Group.objects.create(
            title='test group2',
            slug='test_slug2',
            description='test description',
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_p)
        self.post_list = []
        for post in range(self.POST_COUNT):
            self.post_list.append(
                Post(
                    text=f'Тестовый пост {post}',
                    group=self.group_p,
                    author=self.user_p,
                )
            )
        Post.objects.bulk_create(self.post_list)

    def test_first_p_index_contains_ten_records(self):
        """Проверка количества постов в index на первой странице"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_p_index_contains_ten_records(self):
        """Проверка количества постов в index на второй странице"""
        response = self.authorized_client.get(reverse(
            'posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_first_p_group_contains_ten_records(self):
        """Проверка количества постов в group_list на первой странице"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_p.slug}
                    )
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_p_group_contains_ten_records(self):
        """Проверка количества постов в group_list на первой странице"""
        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.group_p.slug}
                    ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 5)

    def test_first_p_profile_contains_ten_records(self):
        """Проверка количества постов в profile на первой странице"""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user_p.username}
                    )
        )
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_p_profile_contains_ten_records(self):
        """Проверка количества постов в profile на второй странице"""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user_p.username}
                    ) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 5)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewContextTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test group',
            slug='test_slug',
            description='test description',
        )
        cls.group_another = Group.objects.create(
            title='another group',
            slug='another_slug',
            description='another test description',
        )
        small_gif = (            
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_author = PostViewContextTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user_author)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        self.assertEqual(post_author_0, PostViewContextTests.user)
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_group_0, PostViewContextTests.post.group)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        self.assertEqual(post_author_0, PostViewContextTests.user)
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_group_0, PostViewContextTests.post.group)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': PostViewContextTests.user}))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        self.assertEqual(post_author_0, PostViewContextTests.user)
        self.assertEqual(post_text_0, 'Тестовый пост')
        self.assertEqual(post_group_0, PostViewContextTests.post.group)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client_author.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})))
        self.assertEqual(response.context.get('post').author,
                         PostViewContextTests.user
                         )
        self.assertEqual(response.context.get('post').text, 'Тестовый пост')
        self.assertEqual(response.context.get('post').group,
                         PostViewContextTests.post.group
                         )
        self.assertEqual(response.context.get('post').image,
                         PostViewContextTests.post.image
                         )

    def test_post_create_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон create_post(edit) сформирован с правильным контекстом."""
        response = self.authorized_client_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_new_post_arrears_on_pages(self):
        """Созданный пост появился на 3 страницах"""
        reverse_names = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': PostViewContextTests.user})
        ]
        for name in reverse_names:
            with self.subTest():
                response = self.authorized_client_author.get(name)
                first_post = response.context['page_obj'][0]
                first_post_author = first_post.author
                first_post_id = first_post.id
                first_post_group = first_post.group
                first_post_image = first_post.image
                self.assertEqual(first_post_author,
                                 PostViewContextTests.user)
                self.assertEqual(first_post_id, 1)
                self.assertEqual(first_post_group,
                                 PostViewContextTests.post.group)
                self.assertEqual(first_post_image, self.post.image)

    def test_new_post_doesnt_arrears_on_another_group(self):
        """Созданный пост не связан с другой группой"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={
                'slug': self.group_another.slug})
        )
        all_posts_another_g = response.context.get('page_obj').paginator.count
        self.assertEqual(all_posts_another_g, 0)

    def test_new_comment_arrears(self):
        """Созданный коммент появился"""
        response = self.authorized_client_author.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id}))
        first_comment = response.context['comments'][0]
        first_comment_post = first_comment.post
        first_comment_text = first_comment.text
        self.assertEqual(first_comment_post,
                        PostViewContextTests.post)
        self.assertEqual(first_comment_text,
                        PostViewContextTests.comment.text)

    def test_cache(self):
        """Проверка равности кеша"""
        response1 = self.authorized_client_author.get(
            reverse('posts:index')
        )
        first_context = response1.content
        Post.objects.all().delete
        response2 = self.authorized_client_author.get(
            reverse('posts:index')
        )
        second_context = response2.content
        self.assertEqual(first_context, second_context)

    def test_cache_defferent(self):
        """Проверка отличия кеша"""
        response1 = self.authorized_client_author.get(
            reverse('posts:index')
        )
        first_context = response1.content
        Post.objects.all().delete
        cache.clear()
        response2 = self.authorized_client_author.get(
            reverse('posts:index')
        )
        second_context = response2.content
        self.assertEqual(first_context, second_context)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewFollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.user = User.objects.create_user(username='follower')
        cls.group = Group.objects.create(
            title='test group',
            slug='test_slug',
            description='test description',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.follow = Follow.objects.create(
            author=cls.author,
            user=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest = Client()
        self.user = PostViewFollowTests.user
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        self.author = PostViewFollowTests.author
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)
        self.user2 = User.objects.create_user(username='HasNoName')
        self.authorized_user2 = Client()
        self.authorized_user2.force_login(self.user2)

    def test_follower(self):
        """Подписка видна для подписчику"""
        response = self.authorized_user.get(
            reverse('posts:follow_index')
        )
        self.assertIn(self.post, response.context['page_obj'])

    def test_not_follower(self):
        """Подписка не видна для неподписчика"""
        response = self.authorized_user2.get(
            reverse('posts:follow_index')
        )
        all_follows = response.context.get('page_obj').paginator.count
        self.assertEqual(all_follows, 0)

    def test_get_follow(self):
        """Подписка"""
        follow_count = Follow.objects.count()
        response = self.authorized_user2.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author.username})
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(Follow.objects.filter(
            user=self.user2,
            author=self.author,).exists())

    def test_get_unfollow(self):
        """Отписка"""
        Follow.objects.all().delete()
        response = self.authorized_user.get(
            reverse('posts:follow_index')
        )
        all_follows = response.context.get('page_obj').paginator.count
        self.assertEqual(all_follows, 0)
