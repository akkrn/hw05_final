from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserCreateFormTests(TestCase):
    def test_create_user(self):
        """Валидная форма создает пользователя."""
        self.guest_client = Client()
        user_count = User.objects.count()
        form_data = {
            "first_name": "Vasya",
            "last_name": "Pupkin",
            "username": "vasya",
            "email": "vasya@mail.ru",
            "password1": "ER12VIMmogesh",
            "password2": "ER12VIMmogesh",
        }
        response = self.guest_client.post(
            reverse("users:signup"), data=form_data, follow=True
        )
        self.assertRedirects(response, reverse("posts:index"))
        self.assertEqual(User.objects.count(), user_count + 1)
        self.assertTrue(
            User.objects.filter(
                username="vasya", email="vasya@mail.ru"
            ).exists()
        )
