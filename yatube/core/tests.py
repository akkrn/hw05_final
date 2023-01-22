from django.test import Client, TestCase


class CustomErrorPagesURLTests(TestCase):
    url_names = {
        "/unexpected_page/": "core/404.html",
    }

    def setUp(self):
        self.guest_client = Client()

    def test_about_url_uses_correct_template(self):
        """Проверка шаблонов для адресов кастомных страниц ошибок."""
        for address, template in self.url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
