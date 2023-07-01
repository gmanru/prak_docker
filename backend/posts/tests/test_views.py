from http import HTTPStatus
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .. models import Post, Group, Comment, Follow
from posts.forms import PostForm, CommentForm

TEST_OF_POST: int = 13
TEN_POST: int = 10
THREE_POST: int = 3
User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class VIEWSTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user = User.objects.create(username='SnoopDog2')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.group_wihtout_posts = Group.objects.create(
            title='Тестовый заголовок группы без постов',
            slug='no_slug',
            description='Тестовое описание группы без постов'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания нового поста',
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.post.author,
            text='Текст комментария'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='SnoopDog3')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.post.author)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            (reverse('posts:group_list',
                     kwargs={'slug': 'test-slug'})): 'posts/group_list.html',
            (reverse('posts:profile',
                     kwargs={'username': 'SnoopDog2'})): 'posts/profile.html',
            (reverse('posts:post_detail',
                     kwargs={
                         'post_id': self.post.pk})): 'posts/post_detail.html',
            (reverse('posts:post_edit',
                     kwargs={
                         'post_id': self.post.pk})): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Тест контекста для index.html."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

    def test_group_posts_correct_context(self):
        """Тест контекста для group_posts."""
        response = self.authorized_client.get(reverse('posts:group_list',
                                              kwargs={'slug':
                                                      self.group.slug}))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

    def test_profile_correct_context(self):
        """Тест контекста для profile."""
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username':
                                                      self.post.author.username
                                                      }))
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)

    def test_post_detail_correct_context(self):
        """Тест контекста для post_detail."""
        response = self.authorized_client.get(reverse('posts:post_detail',
                                              kwargs={'post_id':
                                                      self.post.id}))
        first_object = response.context['posts']
        self.assertEqual(first_object, self.post)
        self.assertEqual(first_object.author.posts.count(),
                         self.post.author.posts.count())
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)
        self.assertEqual(response.context.get(
            'comments')[0].text,
            'Текст комментария'
        )

    def test_create_correct_context(self):
        """Тест контекста для post_create."""
        response = self.authorized_client.get(reverse(
            'posts:post_create'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)

    def test_edit_correct_context(self):
        """Тест контекста для edit."""
        response = self.authorized_author.get(reverse('posts:post_edit',
                                              kwargs={'post_id':
                                                      self.post.pk}))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertTrue('is_edit')
        self.assertIsInstance(response.context['is_edit'], bool)
        self.assertIn('post', response.context)
        self.assertEqual(response.context['post'], self.post)

    def test_create_post_home_group_list_profile_pages(self):
        """Созданный пост отобразился на главной,
        на странице группы и в профиле пользователя.
        """
        list_urls = (
            reverse('posts:index'),
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.post.author.username}
            ),
        )
        for tested_url in list_urls:
            response = self.authorized_author.get(tested_url)
            self.assertEqual(len(response.context['page_obj'].object_list), 1)

    def test_no_post_in_another_group_posts(self):
        """Пост не попал в группу,
        для которой не был предназначен.
        """
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group_wihtout_posts.slug}))
        posts = response.context['page_obj']
        self.assertEqual(0, len(posts))

    def test_authorized_comment(self):
        """Авторизованный может комментировать"""
        data_comment = {
            'text': 'Комментарий'
        }
        response_authorized = self.authorized_client.post(reverse(
            'posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=data_comment,
            follow=True,
        )
        self.assertEqual(response_authorized.status_code, HTTPStatus.OK)

    def test_guest_comment(self):
        """Не авторизованный не может комментировать"""
        data_comment = {
            'text': 'Комментарий'
        }
        self.guest_client.post(reverse(
            'posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=data_comment,
            follow=True,
        )
        self.assertFalse(Comment.objects.filter(
            text='Комментарий').exists())


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='SnoopDog4')
        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='slug_test',
            description='Тестовое описание')
        cls.posts = []
        for i in range(TEST_OF_POST):
            cls.posts.append(Post(
                text=f'Тестовый пост {i+1}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def test_paginator(self):
        """Тест паджинатора"""
        list_urls = {
            reverse('posts:index'),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug}),
            reverse('posts:profile',
                    kwargs={'username': self.author}),
        }
        for tested_url in list_urls:
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context.get('page_obj'
                                                      ).object_list),
                             TEN_POST)

        for tested_url in list_urls:
            response = self.client.get(tested_url, {'page': 2})
            self.assertEqual(len(response.context.get('page_obj'
                                                      ).object_list),
                             THREE_POST)


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.client_auth_follower.get('/follow/')
        post_text_0 = response.context['page'][0].text
        self.assertEqual(post_text_0, 'Тестовая запись для тестирования ленты')
        # в качестве неподписанного пользователя проверяем собственную ленту
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response,
                               'Тестовая запись для тестирования ленты')
