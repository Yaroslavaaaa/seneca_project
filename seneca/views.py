from django.shortcuts import render
from .serializers import *
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.sites.shortcuts import get_current_site


class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer



    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['status']
    search_fields    = ['name', 'phone']
    ordering_fields  = ['created_at', 'updated_at']
    ordering         = ['-created_at']

    def get_queryset(self):
        current_site = get_current_site(self.request)
        return super().get_queryset().filter(site=current_site)


class BlockViewSet(viewsets.ModelViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer

    def get_queryset(self):
        current_site = get_current_site(self.request)
        return super().get_queryset().filter(site=current_site)


class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.select_related('block').all()
    serializer_class = FloorSerializer

    def get_queryset(self):
        current_site = get_current_site(self.request)
        return super().get_queryset().filter(site=current_site)


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.select_related('floor__block').all()
    serializer_class = PlanSerializer

    def get_queryset(self):
        current_site = get_current_site(self.request)
        return super().get_queryset().filter(site=current_site)
