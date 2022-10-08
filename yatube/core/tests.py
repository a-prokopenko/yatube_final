from django.test import Client, TestCase


class CoreViewTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_404_uses_custom_template(self):
        response = self.guest_client.get('/page_404/')
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)
