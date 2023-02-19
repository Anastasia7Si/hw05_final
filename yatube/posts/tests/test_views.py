import shutil
import tempfile

from django import forms
from django.conf import settings
from http import HTTPStatus
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post, User, Follow, Comment
from posts.views import POSTS_PER_PAGE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
INDEX_URL = reverse('posts:index')
POST_CREATE_URL = reverse('posts:post_create', None)
FOLLOW_URL = reverse('posts:follow_index')
SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
             )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='testAuthor')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='test-slug',
            description='Тест-описание',
        )
        cls.image = SimpleUploadedFile(
            name='small.gif',
            content=SMALL_GIF,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Большой тест-пост',
            group=cls.group,
            image=cls.image,
        )

        cls.GROUP_LIST_URL = reverse(
            'posts:group_list', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.author.username}'}
        )
        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.urls_templates_data = [
            (INDEX_URL, 'posts/index.html'),
            (PostViewsTests.GROUP_LIST_URL, 'posts/group_list.html'),
            (PostViewsTests.PROFILE_URL, 'posts/profile.html'),
            (PostViewsTests.POST_DETAIL_URL, 'posts/post_detail.html'),
            (POST_CREATE_URL, 'posts/create_post.html'),
            (PostViewsTests.POST_EDIT_URL, 'posts/create_post.html'),
            (FOLLOW_URL, 'posts/follow.html'),
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_pages_accessible_by_name(self):
        """Проверяем, что URL, генерируемый при помощи
        имени posts:<name>, доступен."""
        for url, _ in self.urls_templates_data:
            with self.subTest(url=url):
                response = PostViewsTests.author_client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_accordance_templates_reverse(self):
        """Проверяем, что view-функции используют ожидаемые шаблоны."""

        for url, template in self.urls_templates_data:
            with self.subTest(url=url):
                response = PostViewsTests.author_client.get(url)
                self.assertTemplateUsed(
                    response,
                    template
                )

    def context_is_valid(self, context, post=False):
        """Проверяем контекст по ключу 'page_obj' и 'post'."""
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, PostViewsTests.author)
        self.assertEqual(post.group, PostViewsTests.post.group)
        self.assertEqual(post.image, PostViewsTests.post.image)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = PostViewsTests.author_client.get(INDEX_URL)
        self.context_is_valid(response.context)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = PostViewsTests.author_client.get(
            PostViewsTests.GROUP_LIST_URL
        )
        first_group = response.context['group']
        self.context_is_valid(response.context)
        self.assertIsInstance(first_group, Group)
        self.assertEqual(first_group, PostViewsTests.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = PostViewsTests.author_client.get(PostViewsTests.PROFILE_URL)
        self.context_is_valid(response.context)
        self.assertEqual(len(response.context['page_obj']), 1)
        first_author = response.context['author']
        self.assertIsInstance(first_author, User)
        self.assertEqual(first_author, PostViewsTests.author)
        following = response.context['following']
        self.assertIsInstance(following, bool)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        user = User.objects.create_user(username='testAuthorized')
        Comment.objects.create(
            post=PostViewsTests.post,
            author=user,
            text='Тест-комментарий'
        )
        response = PostViewsTests.author_client.get(
            PostViewsTests.POST_DETAIL_URL
        )
        comment = response.context['comments'][0]
        self.context_is_valid(response.context, True)
        self.assertIsInstance(comment, Comment)
        self.assertEqual(comment.author, user)
        self.assertEqual(comment.post, PostViewsTests.post)
        self.assertEqual(response.context['comments'].count(), 1)
        field = response.context['form'].fields['text']
        self.assertIsInstance(field, forms.fields.CharField)

    def form_fields_is_valid(self, url):
        """Проверка типов полей формы."""
        response = PostViewsTests.author_client.get(url)
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        self.form_fields_is_valid(POST_CREATE_URL)

    def test_edit_page_show_correct_context(self):
        """Шаблон create_post на странице редактирования записи
        сформирован с правильным контекстом."""
        self.form_fields_is_valid(PostViewsTests.POST_EDIT_URL)
        response = PostViewsTests.author_client.get(
            PostViewsTests.POST_EDIT_URL
        )
        self.context_is_valid(response.context, True)
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)

    def test_check_group_in_pages(self):
        """Проверка, что запись попала на галвную страницу,
        страницу сообщества и старницу профиля,
        для которых была предназначена."""
        self.post = Post.objects.get(group=self.post.group)
        form_fields = {
            INDEX_URL: self.post,
            PostViewsTests.GROUP_LIST_URL: self.post,
            PostViewsTests.PROFILE_URL: self.post
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.author_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_post_is_not_in_incorrect_group(self):
        """Проверка, что запись не попала на страницу сообщества,
        для которой не была предназначена."""
        self.group2 = Group.objects.create(
            title='Тест-группа2',
            slug='test-slug2',
            description='Тест-описание2',
        )
        group_list_url2 = reverse(
            'posts:group_list', kwargs={'slug': f'{self.group2.slug}'}
        )
        response = PostViewsTests.author_client.get(group_list_url2)
        self.assertEqual(len(response.context['page_obj']), 0)
        group = response.context['group']
        self.assertIsInstance(group, Group)
        self.assertEqual(group, self.group2)

    def test_index_cache(self):
        """Проверяем, что кеширование главной страницы работает."""
        new_post = Post.objects.create(
            text='Комментарий проверки кэша',
            author=PostViewsTests.author,
            group=PostViewsTests.group,
        )
        current_content = PostViewsTests.author_client.get(INDEX_URL).content
        new_post.delete()
        after_delete_post_content = PostViewsTests.author_client.get(
            INDEX_URL).content
        self.assertEqual(current_content, after_delete_post_content)
        cache.clear()
        after_delete_post_content = PostViewsTests.author_client.get(
            INDEX_URL).content
        self.assertNotEqual(current_content, after_delete_post_content)


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testAuthor')
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='test',
            description='Тест-описание',
        )
        cls.GROUP_LIST_URL = reverse(
            'posts:group_list', kwargs={'slug': f'{cls.group.slug}'}
        )
        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.author.username}'}
        )
        cls.ADDPOSTS = 5
        cls.posts = Post.objects.bulk_create(
            Post(
                author=cls.author,
                text=f'{i + 1} большой тест-пост',
                group=cls.group
            )
            for i in range(POSTS_PER_PAGE + cls.ADDPOSTS)
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_accordance_posts_per_pages(self):
        """Проверяем, что количество постов
        на первой странице равно 10, а на второй - 5"""

        for url in [
            INDEX_URL,
            PostPaginatorTests.GROUP_LIST_URL,
            PostPaginatorTests.PROFILE_URL
        ]:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    POSTS_PER_PAGE
                )
                response_second = self.author_client.get(
                    f'{url}?page=2'
                )
                self.assertEqual(
                    len(response_second.context['page_obj']),
                    PostPaginatorTests.ADDPOSTS
                )


class FollowViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testAuthorized')
        cls.author = User.objects.create_user(username='testAuthor')
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='test',
            description='Тест-описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Большой тест-пост',
            group=cls.group,
        )

        cls.PROFILE_URL = reverse(
            'posts:profile', kwargs={'username': f'{cls.author.username}'}
        )
        cls.PROFILE_FOLLOW_URL = reverse(
            'posts:profile_follow',
            kwargs={'username': f'{cls.author.username}'}
        )
        cls.PROFILE_UNFOLLOW_URL = reverse(
            'posts:profile_unfollow',
            kwargs={'username': f'{cls.author.username}'}
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_authorized_follow_author(self):
        """Проверяем, что авторизованный пользователь
        может подписываться на авторов"""
        response = self.authorized_client.post(
            FollowViewsTests.PROFILE_FOLLOW_URL
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=FollowViewsTests.author
            ).exists()
        )
        follow = Follow.objects.latest('id')
        self.assertEqual(follow.user, self.user)
        self.assertEqual(follow.author, FollowViewsTests.author)
        self.assertRedirects(response, FollowViewsTests.PROFILE_URL)

    def test_authorized_unfollow_author(self):
        """Проверяем, что авторизованный пользователь
        может отписываться от авторов"""
        Follow.objects.create(
            user=self.user, author=FollowViewsTests.author
        )
        response = self.authorized_client.post(
            FollowViewsTests.PROFILE_UNFOLLOW_URL
        )
        self.assertEqual(Follow.objects.count(), 0)
        self.assertRedirects(response, FollowViewsTests.PROFILE_URL)

    def test_guest_client_not_allowed_follow_author(self):
        """Проверяем, что незарегистрированный пользователь
        не может подписываться на авторов"""
        follow_guest_redirect_url = (
            f'/auth/login/?next=/profile/{self.author.username}/follow/'
        )
        response = self.guest_client.post(
            FollowViewsTests.PROFILE_FOLLOW_URL
        )
        self.assertEqual(Follow.objects.count(), 0)
        self.assertRedirects(response, follow_guest_redirect_url)

    def test_follow_context(self):
        """Проверяем, что новая запись пользователя появляется
        в ленте тех, кто на него подписан"""
        Follow.objects.create(
            user=self.user,
            author=FollowViewsTests.author
        )
        response = self.authorized_client.get(FOLLOW_URL)
        first_object = response.context['page_obj'][0]
        self.assertEqual(len(response.context['page_obj']), 1)
        self.assertIsInstance(first_object, Post)
        self.assertEqual(first_object.author, FollowViewsTests.author)
        self.assertEqual(first_object.group, FollowViewsTests.group)
        self.assertContains(response, FollowViewsTests.post)

    def test_unfollow_context(self):
        """Проверяем, что новая запись пользователя не появляется
        в ленте тех, кто на него не подписан"""
        response = self.authorized_client.get(FOLLOW_URL)
        self.assertEqual(len(response.context['page_obj']), 0)
        self.assertNotContains(response, FollowViewsTests.post)
