from rest_framework import serializers
from .models import *


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ['id', 'image', 'caption']


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['id', 'youtube_link', 'description', 'year', 'month']


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ['id', 'name', 'phone']


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ['id', 'name']


class FloorSerializer(serializers.ModelSerializer):
    block = BlockSerializer(read_only=True)

    class Meta:
        model = Floor
        fields = ['id', 'block', 'level']


class PlanSerializer(serializers.ModelSerializer):
    floor = FloorSerializer(read_only=True)

    class Meta:
        model = Plan
        fields = ['id', 'floor', 'drawing', 'description']