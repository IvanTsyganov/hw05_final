from django.db import models
from django.contrib.auth import get_user_model
from core.models import CreatedModel

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
        help_text='Название группы'
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='Тег',
        help_text='Тег'
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Описание'
    )

    def __str__(self) -> str:
        return self.title


class Post(CreatedModel):
    text = models.TextField(
        verbose_name='Текст',
        help_text='Текст'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        verbose_name='Картинка',
        help_text='Картинка'
    )

    def __str__(self):
        return self.text[:15]

    class Meta():
        verbose_name = 'Запись'
        verbose_name_plural = 'Записи'
        ordering = ['-pub_date']


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
        help_text='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор',
        help_text='Автор'
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Tекст комментария'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-pub_date']

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
        help_text='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
        help_text='Автор',
    )

    class Meta:
        unique_together = (
            'user',
            'author',
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
