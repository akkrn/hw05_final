from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(
            username="HasNoName",
            email="hasnoname@gmail.com",
            password="123qwerty",
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_password_reset_page_exists_for_clients(self):
        """Страница сброса пароля доступна всем пользователям."""
        client_type = [self.guest_client, self.authorized_client]
        for client in client_type:
            with self.subTest(client=client):
                response = self.client.post(
                    reverse("users:password_reset_form"),
                    {"email": "hasnoname@gmail.com"},
                )
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
                self.assertEqual(
                    mail.outbox[0].subject, "Сброс пароля на testserver"
                )
                token = response.context[0]["token"]
                uid = response.context[0]["uid"]
                response = self.client.get(
                    reverse(
                        "users:password_reset_confirm",
                        kwargs={"uidb64": uid, "token": token},
                    ),
                    follow=True,
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(
                    response, "users/password_reset_confirm.html"
                )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse("users:signup"): "users/signup.html",
            reverse("users:login"): "users/login.html",
            reverse(
                "users:password_change_form"
            ): "users/password_change_form.html",
            reverse(
                "users:password_change_done"
            ): "users/password_change_done.html",
            reverse(
                "users:password_reset_form"
            ): "users/password_reset_form.html",
            reverse(
                "users:password_reset_complete"
            ): "users/password_reset_complete.html",
            reverse(
                "users:password_reset_done"
            ): "users/password_reset_done.html",
            reverse("users:logout"): "users/logged_out.html",
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_initial_value_in_create_post(self):
        """Cтраница регистрации пользователя формирована с правильным
        контекстом."""
        response = self.guest_client.get(reverse("users:signup"))
        form_fields = {
            "first_name": forms.fields.CharField,
            "last_name": forms.fields.CharField,
            "username": forms.fields.CharField,
            "email": forms.fields.EmailField,
            "password1": forms.fields.CharField,
            "password2": forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)
