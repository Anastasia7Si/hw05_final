import shutil
import tempfile

from django.conf import settings
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User, Comment

POST_CREATE_URL = reverse('posts:post_create')

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='testAuthor')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тест-группа',
            slug='test-slug',
            description='Тест-описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Большой тест-пост для проведения тестов',
            group=cls.group,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.small_gif_name = 'small.gif'
        cls.image = 'posts/small.gif'

        cls.POST_DETAIL_URL = reverse(
            'posts:post_detail', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.POST_EDIT_URL = reverse(
            'posts:post_edit', kwargs={'post_id': f'{cls.post.id}'}
        )
        cls.COMMENT = reverse(
            'posts:add_comment', kwargs={'post_id': f'{cls.post.id}'}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testAuthorized')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_create_form(self):
        """Проверяем, что авторизованный пользователь
        создает запись с изображением."""
        test_image = SimpleUploadedFile(
            name=self.small_gif_name,
            content=self.small_gif,
            content_type='image/gif',
        )
        posts_count = Post.objects.count()
        create_form_data = {
            'text': 'Текст авторизованного пользователя',
            'group': PostFormTests.group.pk,
            'image': test_image,
        }
        response = self.authorized_client.post(
            POST_CREATE_URL,
            data=create_form_data,
            follow=True,
        )
        post = Post.objects.latest('pub_date')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(post.text, create_form_data['text'])
        self.assertEqual(post.group.pk, create_form_data['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, PostFormTests.image)

    def test_author_edit_form(self):
        """Проверяем, что автор записи
        редактирует запись."""
        edit_form_data = {
            'text': 'Отредактированный текст',
            'group': self.group.pk,
        }
        edit_response = self.author_client.post(
            PostFormTests.POST_EDIT_URL,
            data=edit_form_data,
        )
        post = Post.objects.latest('pub_date')
        self.assertRedirects(edit_response, PostFormTests.POST_DETAIL_URL)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post.text, edit_form_data['text'])
        self.assertEqual(post.group.pk, edit_form_data['group'])

    def test_authorized_client_comments_post(self):
        """Проверяем, что авторизованный пользователь
        может комментировать записи."""
        text = 'Длинный тест-комментарий'
        commen_form_data = {'text': text}
        commen_response = self.authorized_client.post(
            PostFormTests.COMMENT,
            data=commen_form_data,
            follow=True,
        )
        comment = Comment.objects.latest('created')
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(comment.text, text)
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, PostFormTests.post)
        self.assertRedirects(
            commen_response, PostFormTests.POST_DETAIL_URL
        )

    def test_guest_client_not_allowed_comment_post(self):
        """Проверяем, что незарегистрированный пользователь
        не может комментировать записи."""
        login_url = reverse('login')
        target = f'%2Fposts/{PostFormTests.post.id}/comment/'
        text = 'Тест-комментарий незарегистрированного пользователя'
        comment_form_data = {'text': text}
        comment_response = self.guest_client.post(
            PostFormTests.COMMENT,
            data=comment_form_data,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), 0)
        self.assertRedirects(
            comment_response, f'{login_url}?next={target}')
