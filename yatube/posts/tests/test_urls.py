from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username="HasNoName")
        cls.author = User.objects.create_user(username="Author")
        cls.authorized_client = Client()
        cls.authorized_author = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_author.force_login(cls.author)
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
            description="Тестовый текст",
        )

        cls.post = Post.objects.create(
            text="Тестовый текст",
            author=cls.author,
            group=cls.group,
        )

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /create/ перенаправит анонимного пользователя на
        страницу логина."""
        response = PostsURLTests.guest_client.get("/create/", follow=True)
        self.assertRedirects(response, "/auth/login/?next=/create/")

    def test_unexpected_page_return_404(self):
        """Страница по несуществующему адресу вернут код 404."""
        response = PostsURLTests.guest_client.get("/unexpected_page/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_exists_for_nonauthorized_client(self):
        """Страницы доступны неавторизованному пользователю."""
        url_names = [
            reverse("posts:index"),
            reverse(
                "posts:group_list", kwargs={"slug": PostsURLTests.group.slug}
            ),
            reverse(
                "posts:profile",
                kwargs={"username": PostsURLTests.user.username},
            ),
            reverse(
                "posts:post_detail", kwargs={"post_id": PostsURLTests.post.id}
            ),
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_for_authorized_client(self):
        """Все страницы доступны авторизованному пользователю."""
        url_names = [
            reverse("posts:index"),
            reverse(
                "posts:group_list", kwargs={"slug": PostsURLTests.group.slug}
            ),
            reverse(
                "posts:profile",
                kwargs={"username": PostsURLTests.user.username},
            ),
            reverse(
                "posts:post_detail", kwargs={"post_id": PostsURLTests.post.id}
            ),
            reverse("posts:post_create"),
            reverse(
                "posts:add_comment", kwargs={"post_id": PostsURLTests.post.id}
            ),
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_for_authorized_client(self):
        """Страница редактирования поста доступна только автору."""
        client_type = {
            self.authorized_author: HTTPStatus.OK,
            self.authorized_client: HTTPStatus.FOUND,
            self.guest_client: HTTPStatus.FOUND,
        }
        for client, status in client_type.items():
            with self.subTest(client=client):
                response = client.get(f"/posts/{PostsURLTests.post.id}/edit/")
                self.assertEqual(response.status_code, status)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list", kwargs={"slug": PostsURLTests.group.slug}
            ): "posts/group_list.html",
            reverse(
                "posts:profile",
                kwargs={"username": PostsURLTests.user.username},
            ): "posts/profile.html",
            reverse(
                "posts:post_detail", kwargs={"post_id": PostsURLTests.post.id}
            ): "posts/post_detail.html",
            reverse("posts:post_create"): "posts/post_create.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": PostsURLTests.post.id}
            ): "posts/post_create.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)
