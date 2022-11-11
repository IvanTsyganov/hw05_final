from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Мы мчались, мечтая\n'
            'Постичь поскорей\n'
            'Грамматику пайтон —\n'
            'Язык в IDE.\n'
            'Восход поднимался\n'
            'И падал опять,\n'
            'И лошадь устала\n'
            'по джанге скакать.\n',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        group = PostModelTest.group
        post = PostModelTest.post
        expected_object_name_group = group.title
        expected_object_name_post = post.text[:15]
        self.assertEqual(expected_object_name_post, str(post))
        self.assertEqual(expected_object_name_group, str(group))
