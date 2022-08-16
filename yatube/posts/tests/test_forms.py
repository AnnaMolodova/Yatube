import shutil
import tempfile
from urllib import response

from posts.models import Group, Post, User
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Тест описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тест пост',
            group=cls.group
        )
        cls.gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_create(self):
        """Валидная форма создания поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'текст',
            'author': self.author,
            'group': self.group.id,
        }
        response = self.authorized_client.post(reverse(
            'posts:post_create'
        ), data=form_data, follow=True)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count+1)
        self.assertTrue(
            Post.objects.filter(
                text='текст',
                author=self.author
            ).exists()
        )

    def test_post_edit(self):
        """При редактировании поста запись меняется в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Редактируемый текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(
             reverse(('posts:post_edit'), kwargs={'post_id': self.post.id}),
             data=form_data, follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(1,)
        ))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Редактируемый текст',
                group=self.group.id
            ).exists()
        )
