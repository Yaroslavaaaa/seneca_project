from django.contrib import admin
import openpyxl
from io import BytesIO
from django.http import HttpResponse
from .models import *
from django.shortcuts import redirect, get_object_or_404
from django.utils.html import format_html

# Для WYSIWYG: например, django-ckeditor
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.urls import path, reverse
from .views import *
from django.contrib.admin import AdminSite



admin.site.site_header  = "Seneca Partners CMS"
admin.site.site_title   = "Seneca Admin"
admin.site.index_title  = "Панель управления объектом"
admin.site.site_url = "https://seneca.kz/"




class ObjectAdminSite(AdminSite):
    site_header  = "Админка строй-объекта"
    site_title   = "Строй-CMS"
    index_title  = "Управление контентом"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            # все пути будут автоматически под префиксом /admin/
            path(
                'internal/data-integrity/',
                self.admin_view(DataIntegrityView.as_view()),
                name='data_integrity'
            ),
            path(
                'internal/link-checker/',
                self.admin_view(LinkCheckerView.as_view()),
                name='link_checker'
            ),
            path(
                'reports/applications-summary/',
                self.admin_view(ApplicationSummaryView.as_view()),
                name='applications_summary'
            ),
        ]
        return custom + urls

object_admin = ObjectAdminSite(name='object_admin')

# регистрируем модели
for model in (Block, Floor, Plan, Photo, Video, Application):
    object_admin.register(model)


class SiteAwareAdmin(admin.ModelAdmin):
    list_filter = ('site',)         # возможность быстро выбрать сайт
    readonly_fields = ('site',)


@admin.register(Photo)
class PhotoAdmin(SiteAwareAdmin):
    list_display = ('id', 'caption', 'image')
    search_fields = ('caption',)

@admin.register(Video)
class VideoAdmin(SiteAwareAdmin):
    list_display = ('id', 'youtube_link', 'year', 'month')
    list_filter = ('year', 'month')
    search_fields = ('youtube_link', 'description')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display   = ('id', 'name', 'phone', 'status', 'created_at')
    list_filter    = ('status', 'created_at')
    search_fields  = ('name', 'phone')
    fields          = ('name', 'phone', 'status', 'comment')
    actions        = ['export_applications_xlsx']

    def export_applications_xlsx(self, request, queryset):
        """
        Экспорт выбранных заявок в файл Excel (XLSX).
        """
        # 1) Создаём книгу и лист
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'Заявки'

        # 2) Заголовки столбцов
        headers = [
            'ID', 'Имя', 'Телефон', 'Статус',
            'Комментарий', 'Дата создания'
        ]
        ws.append(headers)

        # 3) Данные заявок
        for obj in queryset.order_by('-created_at'):
            ws.append([
                obj.id,
                obj.name,
                obj.phone,
                obj.get_status_display(),
                obj.comment,
                obj.created_at.strftime('%Y-%m-%d %H:%M'),
            ])

        # 4) Сохраняем в поток и возвращаем как Response
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="applications.xlsx"'
        return response

    export_applications_xlsx.short_description = "Экспорт заявок в Excel"

@admin.register(Block)
class BlockAdmin(SiteAwareAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Floor)
class FloorAdmin(SiteAwareAdmin):
    list_display = ('id', 'block', 'level')
    list_filter = ('block', 'level')
    search_fields = ('block__name', 'level')

@admin.register(Plan)
class PlanAdmin(SiteAwareAdmin):
    list_display = ('id', 'floor', 'description')
    list_filter = ('floor__block', 'floor__level')
    search_fields = ('description',)




class ProposalTemplateForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget())

    class Meta:
        model  = ProposalTemplate
        fields = '__all__'


@admin.register(ProposalTemplate)
class ProposalTemplateAdmin(admin.ModelAdmin):
    form = ProposalTemplateForm
    list_display = ('name', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display   = ('id', 'block', 'floor', 'area', 'finish_level',
                      'total_price', 'download_link', 'created_at')
    list_filter    = ('block', 'floor', 'finish_level', 'created_at')
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
            path(
                '<int:pk>/generate/',
                self.admin_site.admin_view(self.process_generate),
                name='proposal-generate',
            ),
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
    generate_button.allow_tags = True

    def process_generate(self, request, pk):
        proposal = get_object_or_404(Proposal, pk=pk)
        proposal.generate_pdf()
        self.message_user(request, "PDF сгенерирован и сохранён.")
        return redirect(request.META.get('HTTP_REFERER'))

    def download_link(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank">Скачать</a>',
                obj.pdf_file.url
            )
        return "-"
    download_link.short_description = "PDF"