from django.test import Client, TestCase
from django.urls import reverse


class AboutViewTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_url_uses_correct_template(self):
        """Проверка шаблонов статичных страниц"""
        templates_url_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
