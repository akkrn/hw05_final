from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UsersURLTests(TestCase):
    def setUp(self):
        super().setUpClass()
        self.guest_client = Client()
        self.user = User.objects.create_user(
            username="HasNoName",
            email="hasnoname@gmail.com",
            password="123qwerty",
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_url_redirect_anonymous_on_auth_login(self):
        """Страница по адресу /auth/password_change/ перенаправит анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get("/auth/password_change/", follow=True)
        self.assertRedirects(
            response, "/auth/login/?next=/auth/password_change/"
        )

    def test_url_exists_for_nonauthorized_client(self):
        """Страницы доступны неавторизованному пользователю."""
        url_names = [
            reverse("users:signup"),
            reverse("users:logout"),
            reverse("users:login"),
            reverse("users:password_change_done"),
            reverse("users:password_reset_form"),
            reverse("users:password_reset_complete"),
            reverse("users:password_reset_done"),
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_for_authorized_client(self):
        """Все страницы доступны авторизованному пользователю."""
        url_names = [
            reverse("users:signup"),
            reverse("users:login"),
            reverse("users:password_change_form"),
            reverse("users:password_change_done"),
            reverse("users:password_reset_form"),
            reverse("users:password_reset_complete"),
            reverse("users:password_reset_done"),
            reverse("users:logout"),
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
