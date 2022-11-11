from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from http import HTTPStatus
from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
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
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_author = PostURLTests.user
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.user_author)

    def test_urls_guest_client(self):
        """URL видимые всем"""
        urls = {
            '/',
            f'/profile/{self.user.username}/',
            f'/group/{self.group.slug}/',
            f'/posts/{self.post.id}/',
        }
        for url in urls:
            with self.subTest():
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_client(self):
        """URL видимые авторизованному"""
        urls = [
            '/create/',
            '/follow/',
        ]
        for url in urls:
            with self.subTest():
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_for_author_only_redirect(self):
        """URL /edit/ редирект авторизованного"""
        response = self.authorized_client.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_for_author_only(self):
        """URL /edit/ доступ автору"""
        response = self.authorized_client_author.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_client(self):
        """URL /create/ редирект анона"""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_unexisting_gape(self):
        """URL несуществующие страницы"""
        response_anon = self.guest_client.get('/unexisting_page/')
        response_user = self.authorized_client.get('/unexisting_page/')
        response_author = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response_anon.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response_user.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response_author.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/post_create.html',
            '/create/': 'posts/post_create.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)
