from django.shortcuts import render
from .serializers import *
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
import re
import requests
from urllib.parse import urlencode
from django.db.models import F, DurationField, ExpressionWrapper, Avg, Count, Q
import datetime
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.permissions import IsAdminUser




class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)

class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsAdminOrReadOnly]


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAdminOrReadOnly]


class ApplicationViewSet(viewsets.ModelViewSet):

    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [IsAdminOrReadOnly]



    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ['status']
    search_fields    = ['name', 'phone']
    ordering_fields  = ['created_at', 'updated_at']
    ordering         = ['-created_at']




class BlockViewSet(viewsets.ModelViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        current_site = get_current_site(self.request)
        return super().get_queryset().filter(site=current_site)


class FloorViewSet(viewsets.ModelViewSet):
    queryset = Floor.objects.select_related('block').all()
    serializer_class = FloorSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        current_site = get_current_site(self.request)
        return super().get_queryset().filter(site=current_site)


class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.select_related('floor__block').all()
    serializer_class = PlanSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        current_site = get_current_site(self.request)
        return super().get_queryset().filter(site=current_site)




@method_decorator(staff_member_required, name='dispatch')
class DataIntegrityView(TemplateView):
    template_name = 'data_integrity.html'
    permission_classes = [IsAdminUser]

    def get_context_data(self, **kwargs):
        floors_missing_plan = Floor.objects.filter(plan__isnull=True)
        blocks_without_floors = Block.objects.filter(floors__isnull=True)

        return {
            'floors_missing_plan': floors_missing_plan,
            'blocks_without_floors': blocks_without_floors,
        }

    def render_to_response(self, context, **response_kwargs):
        req = self.request
        want_json = req.GET.get('format') == 'json' or \
                    req.headers.get('Accept', '').startswith('application/json')
        if want_json:
            def serialize_floor(f):
                return {
                    'id': f.id,
                    'block': f.block.name,
                    'level': f.get_level_display(),
                }
            def serialize_block(b):
                return {
                    'id': b.id,
                    'name': b.name,
                }
            data = {
                'floors_missing_plan': [
                    serialize_floor(f) for f in context['floors_missing_plan']
                ],
                'blocks_without_floors': [
                    serialize_block(b) for b in context['blocks_without_floors']
                ],
            }
            return JsonResponse(data)

        return super().render_to_response(context, **response_kwargs)








@method_decorator(staff_member_required, name='dispatch')
class LinkCheckerView(TemplateView):
    template_name = 'link_checker.html'
    timeout = 3
    URL_PATTERN = re.compile(r'https?://[^\s\'"]+')
    permission_classes = [IsAdminUser]

    def extract_urls(self):
        urls = []
        for v in Video.objects.all():
            urls.append({
                'model': 'Video',
                'id': v.id,
                'field': 'youtube_link',
                'url': v.youtube_link,
            })
            # 2) любые URL в description
            for match in self.URL_PATTERN.findall(v.description or ''):
                urls.append({
                    'model': 'Video',
                    'id': v.id,
                    'field': 'description',
                    'url': match,
                })

        # 3) URL внутри Plan.description
        for p in Plan.objects.all():
            for match in self.URL_PATTERN.findall(p.description or ''):
                urls.append({
                    'model': 'Plan',
                    'id': p.id,
                    'field': 'description',
                    'url': match,
                })

        return urls

    def check_youtube_oembed(self, url):

        params = {'url': url, 'format': 'json'}
        oembed_url = f'https://www.youtube.com/oembed?{urlencode(params)}'
        try:
            resp = requests.get(oembed_url, timeout=self.timeout)
            return resp.status_code
        except Exception as e:
            return f'oEmbed error: {e}'

    def check_url(self, url):
        head_error = None

        try:
            head = requests.head(url, allow_redirects=True, timeout=self.timeout)
            if 200 <= head.status_code < 400:
                if 'youtube.com' in url or 'youtu.be' in url:
                    return self.check_youtube_oembed(url)
                return head.status_code
        except Exception as e:
            head_error = str(e)

        try:
            get = requests.get(url, allow_redirects=True, timeout=self.timeout)
            return get.status_code
        except Exception as e_get:
            return head_error or str(e_get)

    def get_context_data(self, **kwargs):
        to_check = self.extract_urls()
        results = []
        for item in to_check:
            status = self.check_url(item['url'])
            ok = isinstance(status, int) and 200 <= status < 400
            results.append({**item, 'status': status, 'ok': ok})

        broken = [r for r in results if not r['ok']]
        return {'results': results, 'broken': broken}

    def render_to_response(self, context, **response_kwargs):
        req = self.request
        want_json = (
            req.GET.get('format') == 'json' or
            req.headers.get('Accept', '').startswith('application/json')
        )
        if want_json:
            return JsonResponse({
                'all_checked': context['results'],
                'broken': context['broken'],
            }, safe=False)
        return super().render_to_response(context, **response_kwargs)




# views.py

@method_decorator(staff_member_required, name='dispatch')
class ApplicationSummaryView(TemplateView):
    template_name = 'applications_summary.html'
    permission_classes = [IsAdminUser]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs  = Application.objects.all()

        start_str = self.request.GET.get('start_date')
        end_str   = self.request.GET.get('end_date')

        try:
            if start_str:
                start = datetime.datetime.strptime(start_str, '%Y-%m-%d').date()
                qs = qs.filter(created_at__date__gte=start)
            if end_str:
                end = datetime.datetime.strptime(end_str, '%Y-%m-%d').date()
                qs = qs.filter(created_at__date__lte=end)
        except ValueError:
            start_str = end_str = None

        ctx.update({
            'start_date': start_str or '',
            'end_date':   end_str   or '',
        })

        total_count  = qs.count()
        closed_count = qs.filter(status=Application.STATUS_CLOSED).count()
        conversion   = (closed_count / total_count * 100) if total_count else 0

        closed_qs = qs.filter(status=Application.STATUS_CLOSED).annotate(
            processing_time=ExpressionWrapper(
                F('updated_at') - F('created_at'),
                output_field=DurationField()
            )
        )
        avg_duration = closed_qs.aggregate(avg_time=Avg('processing_time'))['avg_time']

        if avg_duration:
            secs   = avg_duration.total_seconds()
            days   = avg_duration.days
            hours  = int(secs // 3600) % 24
            mins   = int((secs % 3600) // 60)
            secs_r = int(secs % 60)
        else:
            days = hours = mins = secs_r = None

        ctx.update({
            'total_count':         total_count,
            'closed_count':        closed_count,
            'conversion_rate':     round(conversion, 2),
            'avg_processing_time': avg_duration,
            'avg_days':            days,
            'avg_hours':           hours,
            'avg_minutes':         mins,
            'avg_seconds':         secs_r,
        })
        return ctx

    def render_to_response(self, context, **response_kwargs):
        req       = self.request
        want_json = req.GET.get('format') == 'json' or \
                    req.headers.get('Accept', '').startswith('application/json')

        if want_json:
            data = {
                'start_date':            context['start_date'],
                'end_date':              context['end_date'],
                'total_applications':    context['total_count'],
                'closed_applications':   context['closed_count'],
                'conversion_rate_%':     context['conversion_rate'],
                'avg_processing_secs':   (
                    context['avg_processing_time'].total_seconds()
                    if context['avg_processing_time'] else None
                ),
            }
            return JsonResponse(data)

        return super().render_to_response(context, **response_kwargs)