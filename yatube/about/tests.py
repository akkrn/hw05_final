from http import HTTPStatus

from django.test import Client, TestCase


class StaticPagesURLTests(TestCase):
    url_names = {
        "/about/author/": "about/author.html",
        "/about/tech/": "about/tech.html",
    }

    def setUp(self):
        self.guest_client = Client()

    def test_about_url_exists_at_desired_location(self):
        """Проверка доступности адресов статичных страниц."""
        for address in self.url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_url_uses_correct_template(self):
        """Проверка шаблонов для адресов статичных страниц."""
        for address, template in self.url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
