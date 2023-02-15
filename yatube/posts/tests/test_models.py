from django.test import TestCase

from posts.models import Group, Post, User, Comment, Follow


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='Тест-слаг',
            description='Тест-описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест-пост',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тест-комментарий',
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.author,
        )

        cls.LENGTH_TEXT = 15

    def test_post_have_correct_str_text(self):
        """Проверяем __str__"""
        data = {
            'post': (
                self.post.__str__(),
                self.post.text[:PostModelTest.LENGTH_TEXT]
            ),
            'group': (
                self.group.__str__(),
                self.group.title
            ),
        }

        for key, value in data.items():
            actual_value, expected = value
            with self.subTest(
                model=key, expected=expected, actual_value=actual_value
            ):
                self.assertEqual(expected, actual_value)

    def test_post_verbose_name(self):
        """Проверяем verbose_name записи"""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Запись',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_group_verbose_name(self):
        """Проверяем verbose_name группы"""
        group = PostModelTest.group
        field_verboses = {
            'title': 'Имя группы',
            'slug': 'Адрес',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_comment_verbose_name(self):
        """Проверяем verbose_name комментария"""
        comment = PostModelTest.comment
        field_verboses = {
            'post': 'Запись',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата публикации комментария',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    comment._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_follow_verbose_name(self):
        """Проверяем verbose_name подписки"""
        follow = PostModelTest.follow
        field_verboses = {
            'user': 'Подписчик',
            'author': 'Автор',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    follow._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_post_help_text(self):
        """Проверяем help_text записи"""
        post = PostModelTest.post
        field_help = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in field_help.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )

    def test_comment_help_text(self):
        """Проверяем help_text комментария"""
        comment = PostModelTest.comment
        help_text = comment._meta.get_field('text').help_text
        self.assertEqual(help_text, 'Пожалуйста, оставьте Ваш комментарий')
