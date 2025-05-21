from django.contrib import admin
import openpyxl
from io import BytesIO
from django.http import HttpResponse
from .models import *
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import format_html
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.urls import path, reverse
from .views import *
from django.contrib.admin import AdminSite


class ObjectAdminSite(AdminSite):
    site_header = "Админка строй-объекта"
    site_title = "Строй-CMS"
    index_title = "Управление контентом"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('internal/data-integrity/', self.admin_view(DataIntegrityView.as_view()), name='data_integrity'),
            path('internal/link-checker/', self.admin_view(LinkCheckerView.as_view()), name='link_checker'),
            path('reports/applications-summary/', self.admin_view(ApplicationSummaryView.as_view()), name='applications_summary'),
        ]
        return custom + urls

object_admin = ObjectAdminSite(name='object_admin')


@admin.action(description="Экспорт выбранных заявок в Excel")
def export_applications_xlsx(modeladmin, request, queryset):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Заявки'

    headers = ['ID', 'Имя', 'Телефон', 'Статус', 'Комментарий', 'Дата создания']
    ws.append(headers)

    for obj in queryset.order_by('-created_at'):
        ws.append([
            obj.id,
            obj.name,
            obj.phone,
            obj.get_status_display(),
            obj.comment,
            obj.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="applications.xlsx"'
    return response


class SiteAwareAdmin(admin.ModelAdmin):
    list_filter = ('site',)
    readonly_fields = ('site',)


class PhotoAdmin(SiteAwareAdmin):
    list_display = ('id', 'caption', 'image')
    search_fields = ('caption',)


class VideoAdmin(SiteAwareAdmin):
    list_display = ('id', 'youtube_link', 'year', 'month')
    list_filter = ('year', 'month')
    search_fields = ('youtube_link', 'description')


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'phone')
    fields = ('name', 'phone', 'status', 'comment')
    actions = [export_applications_xlsx]


class BlockAdmin(SiteAwareAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


class FloorAdmin(SiteAwareAdmin):
    list_display = ('id', 'block', 'level')
    list_filter = ('block', 'level')
    search_fields = ('block__name', 'level')


class PlanAdmin(SiteAwareAdmin):
    list_display = ('id', 'floor', 'description')
    list_filter = ('floor__block', 'floor__level')
    search_fields = ('description',)


class ProposalTemplateForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model = ProposalTemplate
        fields = '__all__'


class ProposalTemplateAdmin(admin.ModelAdmin):
    form = ProposalTemplateForm
    list_display = ('name', 'created_at')
    readonly_fields = ('created_at',)


class ProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'block', 'floor', 'area', 'finish_level', 'total_price', 'download_link', 'created_at')
    list_filter = ('block', 'floor', 'finish_level', 'created_at')
    readonly_fields = ('price_per_m2', 'total_price', 'pdf_file', 'created_at', 'generate_button')

    fields = (
        'template', 'application',
        'block', 'floor', 'area', 'finish_level',
        'price_per_m2', 'total_price',
        'generate_button', 'pdf_file',
        'created_at',
    )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:pk>/generate/', self.admin_site.admin_view(self.process_generate), name='proposal-generate'),
        ]
        return custom + urls

    def generate_button(self, obj):
        if obj.pk:
            return format_html(
                '<a class="button" href="{}">Сгенерировать PDF</a>',
                reverse('admin:proposal-generate', args=[obj.pk])
            )
        return "Сохраните сначала, чтобы сгенерировать"
    generate_button.short_description = "Генерация PDF"

    def process_generate(self, request, pk):
        proposal = get_object_or_404(Proposal, pk=pk)
        proposal.generate_pdf()
        self.message_user(request, "PDF сгенерирован и сохранён.")
        return redirect(request.META.get('HTTP_REFERER'))

    def download_link(self, obj):
        if obj.pdf_file:
            return format_html('<a href="{}" target="_blank">Скачать</a>', obj.pdf_file.url)
        return "-"
    download_link.short_description = "PDF"


class BankAdmin(admin.ModelAdmin):
    list_display = ('name', 'rate')
    search_fields = ('name',)


object_admin.register(Photo, PhotoAdmin)
object_admin.register(Video, VideoAdmin)
object_admin.register(Application, ApplicationAdmin)
object_admin.register(Block, BlockAdmin)
object_admin.register(Floor, FloorAdmin)
object_admin.register(Plan, PlanAdmin)
object_admin.register(ProposalTemplate, ProposalTemplateAdmin)
object_admin.register(Proposal, ProposalAdmin)
object_admin.register(Bank, BankAdmin)
