import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post
from posts.forms import PostForm

from http import HTTPStatus

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='DogSnoops')
        cls.group = Group.objects.create(
            title='Тестовый титул',
            slug='test_slag',
            description='Тестовое описание'
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_post(self):
        """При создании валидной формы создается запись в бд"""
        count = Post.objects.count()
        form_data = {
            'text': 'Сообщение',
            'group': self.group.id,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post = Post.objects.get(text='Сообщение')
        self.assertEqual(Post.objects.count(), count + 1)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': 'DogSnoops'}))
        self.assertEqual(post.text, form_data['text'])

    def test_guest_new_post(self):
        """Гостевой пользователь не может создавать посты"""
        form_data = {
            'text': 'Пост от гостевого пользователя',
            'group': self.group.id
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
            text='Пост от гостевого пользователя').exists())

    def test_authorized_edit_post(self):
        """Авторизованный пользователь может редактировать пост"""
        form_data = {
            'text': 'Сообщение2',
            'group': self.group.id
        }
        self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_two = Post.objects.get(text='Сообщение2')
        self.client.get(f'/posts/{post_two.id}/edit')
        form_data = {
            'text': 'Измененное сообщение',
            'group': self.group.id
        }
        response_edit = self.author_client.post(
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': post_two.id
                    }),
            data=form_data,
            follow=True,
        )
        post_two = Post.objects.get(text='Измененное сообщение')
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertEqual(post_two.text, form_data['text'])

    def test_post_with_picture(self):
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
        form_data = {
            'text': 'Пост с картикой',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        post = Post.objects.get(text='Пост с картикой')
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': 'DogSnoops'}))
        self.assertEqual(post.text, form_data['text'])
