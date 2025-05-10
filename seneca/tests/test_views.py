from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from seneca.models import Application, Block, Floor, Plan
import json

class ViewsTestCase(TestCase):
    def setUp(self):
        # создаём staff-пользователя для @staff_member_required views
        self.admin = User.objects.create_user('admin', password='pass')
        self.admin.is_staff = True
        self.admin.save()

        # тестовый клиент
        self.client = Client()
        self.client.login(username='admin', password='pass')

        # несколько заявок
        Application.objects.create(name='A', phone='1', status=Application.STATUS_NEW)
        Application.objects.create(name='B', phone='2', status=Application.STATUS_CLOSED)

    def test_data_integrity_view_html_and_json(self):
        url = reverse('object_admin:data_integrity')
        # HTML
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # JSON
        resp_json = self.client.get(f'{url}?format=json', HTTP_ACCEPT='application/json')
        data = resp_json.json()
        self.assertIn('floors_missing_plan', data)
        self.assertIn('blocks_without_floors', data)

    def test_applications_summary_default(self):
        url = reverse('object_admin:applications_summary')
        resp = self.client.get(f'{url}?format=json')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('total_applications', data)
        self.assertIn('closed_applications', data)
        self.assertIn('conversion_rate_%', data)
        self.assertIn('avg_processing_secs', data)

    def test_application_api_crud(self):
        # список
        resp = self.client.get('/api/applications/')
        self.assertEqual(resp.status_code, 200)
        # создание
        payload = {'name':'C','phone':'3'}
        resp2 = self.client.post('/api/applications/', data=json.dumps(payload),
                                 content_type='application/json')
        self.assertEqual(resp2.status_code, 201)
        # деталка
        obj_id = resp2.json()['id']
        resp3 = self.client.get(f'/api/applications/{obj_id}/')
        self.assertEqual(resp3.status_code, 200)
