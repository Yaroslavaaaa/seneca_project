from django.contrib import admin
from .models import *

# Register your models here.


admin.site.site_header  = "Seneca Partners CMS"
admin.site.site_title   = "Seneca Admin"
admin.site.index_title  = "Панель управления объектом"
admin.site.site_url = "https://seneca.kz/"



@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'caption', 'image')
    search_fields = ('caption',)

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('id', 'youtube_link', 'year', 'month')
    list_filter = ('year', 'month')
    search_fields = ('youtube_link', 'description')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'phone')
    search_fields = ('name', 'phone')

@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ('id', 'block', 'level')
    list_filter = ('block', 'level')
    search_fields = ('block__name', 'level')

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'floor', 'description')
    list_filter = ('floor__block', 'floor__level')
    search_fields = ('description',)


@admin.register(ProposalTemplate)
class ProposalTemplateAdmin(admin.ModelAdmin):
    list_display    = ('name', 'created_at')
    search_fields   = ('name',)
    readonly_fields = ('created_at',)

@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display     = (
        'id', 'template', 'application', 'block', 'floor',
        'area', 'finish_level', 'price_per_m2', 'total_price',
        'created_at'
    )
    list_filter      = ('template', 'finish_level', 'created_at')
    search_fields    = (
        'template__name',
        'application__id',
        'block__name',
        'floor__level',
    )
    readonly_fields  = ('created_at', 'total_price')
    autocomplete_fields = ('template', 'application', 'block', 'floor')

    fieldsets = (
        (None, {
            'fields': ('template', 'application', 'block', 'floor')
        }),
        ('Параметры', {
            'fields': ('area', 'finish_level', 'price_per_m2', 'total_price')
        }),
        ('Документ', {
            'fields': ('pdf_file',)
        }),
        ('Системное', {
            'fields': ('created_at',)
        }),
    )
