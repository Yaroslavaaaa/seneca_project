from django.test import TestCase
from seneca.models import *
from seneca.serializers import *
from django.contrib.sites.models import Site

class SerializersTestCase(TestCase):
    def setUp(self):
        self.photo = Photo.objects.create(site=Site.objects.first(), caption='Cap', image='')
        self.video = Video.objects.create(site=Site.objects.first(), youtube_link='http://youtu.be/x', year='2025', month='May')
        self.app   = Application.objects.create(name='Тест', phone='123')
        block = Block.objects.create(site=Site.objects.first(), name='C')
        floor = Floor.objects.create(site=Site.objects.first(), block=block, level='mansard')
        self.plan  = Plan.objects.create(site=Site.objects.first(), floor=floor, description='Desc')

    def test_photo_serializer(self):
        data = PhotoSerializer(self.photo).data
        self.assertEqual(data['caption'], 'Cap')

    def test_video_serializer(self):
        data = VideoSerializer(self.video).data
        self.assertEqual(data['year'], '2025')

    def test_application_serializer_readonly(self):
        data = ApplicationSerializer(self.app).data
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def test_nested_floor_plan_serializer(self):
        data = PlanSerializer(self.plan).data
        self.assertIn('floor', data)
        self.assertIn('id', data['floor'])
