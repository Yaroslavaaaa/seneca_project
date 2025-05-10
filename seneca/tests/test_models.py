from django.test import TestCase
from django.contrib.sites.models import Site
from seneca.models import *


class ModelsTestCase(TestCase):


    def setUp(self):

        self.site, _ = Site.objects.get_or_create(
        domain = 'example.com',
        defaults = {'name': 'example'}
        )

    def test_application_str_and_default_status(self):
        app = Application.objects.create(name='Иван', phone='+77001234567')
        self.assertEqual(app.status, Application.STATUS_NEW)
        self.assertEqual(str(app), 'Иван — +77001234567')

    def test_floor_plan_relationship(self):
        block = Block.objects.create(site=self.site, name='A')
        floor = Floor.objects.create(site=self.site, block=block, level='1')
        plan = Plan.objects.create(site=self.site, floor=floor, description='Test')
        self.assertEqual(floor.plan, plan)
        self.assertEqual(str(plan), f'Чертеж для {floor}')

    def test_plan_price_per_m2_field(self):
        block = Block.objects.create(site=self.site, name='B')
        floor = Floor.objects.create(site=self.site, block=block, level='2')
        plan = Plan.objects.create(site=self.site, floor=floor, price_per_m2=1500)
        self.assertEqual(plan.get_price_per_m2(), 1500)
