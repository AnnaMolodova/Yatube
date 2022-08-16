from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostUrlTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="author")

        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовое описание",
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая пост",
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL адрес использует нужный шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
            'posts/create_post.html': f'/posts/{self.post.id}/edit/',
            'posts/create_post.html': '/create/',
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_guest(self):
        """Страницы, доступные для гостя."""
        page_guest = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        ]
        for address in page_guest:
            response = self.guest_client.get(address)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized(self):
        """Страница для авторизованного пользователя."""
        responses = {
            self.authorized_client.get('/create/'),
        }
        for response in responses:
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Вернет 404, если страницы не существует."""
        response_guest = self.guest_client.get('/unexisting_page/')
        response_auth = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response_guest.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(response_auth.status_code, HTTPStatus.NOT_FOUND)

    def test_post_edit(self):
        """Шаблон и страница автора доступна только ему
        для редактирования."""
        address = f'/posts/{self.post.id}/edit/'
        template = 'posts/create_post.html'
        response = self.authorized_client.get(address)
        self.assertTemplateUsed(response, template)
        self.assertEqual(response.status_code, HTTPStatus.OK)
