from django.test import Client, TestCase


class CoreViewTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_uses_custom_template(self):
        urls_template = {
            '/page_404/': 'core/404.html',
        }
        for url, template in urls_template.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
