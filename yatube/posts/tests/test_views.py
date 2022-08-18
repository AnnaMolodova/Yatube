from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Вот такой текст',
            pub_date='15.12.2001',
        )

        cls.templates_pages_name = {
             reverse('posts:index'): 'posts/index.html',
             (reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
             )): 'posts/group_list.html',
             (reverse(
                'posts:post_create'
                )): 'posts/create_post.html',
             (reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.pk}
             )): 'posts/post_detail.html',
             (reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.pk}
             )): 'posts/create_post.html',
             (reverse(
                'posts:profile',
                kwargs={'username': cls.user.username}
             )): 'posts/profile.html',
        }

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_name.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        """Вернет 404, если страницы не существует."""
        response_auth = self.authorized_client.get('/unexisting_page/')
        self.assertEqual(response_auth.status_code, HTTPStatus.NOT_FOUND)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        post = response.context['page_obj'][0].text
        self.assertEqual(post, 'Вот такой текст')

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        group = response.context['page_obj'][0].group.title
        self.assertEqual(group, 'Тест группа')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        user = response.context['page_obj'][0].author
        self.assertEqual(user, self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        post_detail = response.context['post'].text
        self.assertEqual(post_detail, 'Вот такой текст')

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = (
                    response.context.get('form').fields.get(value)
                )
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = (
                    response.context.get('form').fields.get(value)
                )
                self.assertIsInstance(form_field, expected)

    def test_post_with_group_in_index_page(self):
        """Пост с группой есть на главной странице."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        post = response.context['page_obj'][0]
        post_group = post.group.title
        post_text = post.text
        post_author = post.author.username
        self.assertEqual(post_group, 'Тест группа')
        self.assertEqual(post_text, 'Вот такой текст')
        self.assertEqual(post_author, 'auth')

    def test_post_with_group_in_group_list_page(self):
        """Пост с группой есть на странице c выбранной группой."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test-slug'})
        )
        post = response.context['page_obj'][0]
        post_group = post.group.title
        post_text = post.text
        post_author = post.author.username
        self.assertEqual(post_group, 'Тест группа')
        self.assertEqual(post_text, 'Вот такой текст')
        self.assertEqual(post_author, 'auth')

    def test_post_with_group_in_profile_page(self):
        """Пост с группой есть на странице пользователя."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'})
        )
        post = response.context['page_obj'][0]
        post_group = post.group.title
        post_text = post.text
        post_author = post.author.username
        self.assertEqual(post_group, 'Тест группа')
        self.assertEqual(post_text, 'Вот такой текст')
        self.assertEqual(post_author, 'auth')


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        example_obj = []
        for i in range(0, 13):
            cls.post = Post(
                author=cls.user,
                group=cls.group,
                text=f'{i }Вот такой текст',
                pub_date='15.12.2001',
            )
            example_obj.append(cls.post)
        Post.objects.bulk_create(example_obj)
        # Созданы объекты bulk_create

        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_first_index_page_contains_ten_records(self):
        """Количество постов на первой странице index равно 10."""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_index_page_contains_three_records(self):
        """Количество постов на второй странице index равно 3."""
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_list_page_contains_ten_records(self):
        """Количество постов на первой странице group_list равно 10."""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}
        ))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_list_page_contains_three_records(self):
        """Количество постов на второй group_list странице равно 3."""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_profile_page_ten_records(self):
        """Количество постов на первой странице profile равно 10."""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'auth'}
        ))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_contains_three_records(self):
        """Количество постов на второй profile странице равно 3."""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': 'auth'}) + '?page=2'
        )
        self.assertEqual(len(response.context['page_obj']), 3)
