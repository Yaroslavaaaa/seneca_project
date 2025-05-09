from django.db import models
from django.urls import reverse
from django.template import Template, Context
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from django.utils.html import strip_tags
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
import os, io, html


# Platypus
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from django.contrib.sites.models import Site


FONT_PATH = os.path.join(
    settings.BASE_DIR,
    'seneca',
    'fonts',
    'DejaVuSans.ttf'
)
pdfmetrics.registerFont(TTFont('DejaVuSans', FONT_PATH))


class SiteAware(models.Model):
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        default=settings.SITE_ID,
        editable=False,
        db_index=True,
    )

    class Meta:
        abstract = True

#Dilnaz
class Photo(SiteAware):
    image = models.ImageField(upload_to='photos/')
    caption = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.caption or "Фото без подписи"

class Video(SiteAware):
    youtube_link = models.URLField()
    description = models.TextField(blank=True)
    year = models.CharField(max_length=4)
    month = models.CharField(max_length=20)

    def __str__(self):
        return self.youtube_link

class Application(models.Model):
    STATUS_NEW      = 'new'
    STATUS_IN_WORK  = 'in_work'
    STATUS_CLOSED   = 'closed'
    STATUS_CHOICES = [
        (STATUS_NEW,     'Новая'),
        (STATUS_IN_WORK, 'В работе'),
        (STATUS_CLOSED,  'Закрыта'),
    ]

    name       = models.CharField('Имя', max_length=100)
    phone      = models.CharField('Телефон', max_length=20)
    status     = models.CharField('Статус', max_length=10,
                                  choices=STATUS_CHOICES,
                                  default=STATUS_NEW)
    comment    = models.TextField('Комментарий менеджера',
                                  blank=True)
    created_at = models.DateTimeField('Дата создания',
                                      auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления',
                                      auto_now=True)

    def __str__(self):
        return f'{self.name} — {self.phone}'

    def get_absolute_url(self):
        # для редиректа после создания
        return reverse('thanks')



class Block(SiteAware):
    name = models.CharField(max_length=1)

    def __str__(self):
        return f'Блок {self.name}'


class Floor(SiteAware):
    FLOOR_CHOICES = [
        ('1', '1 этаж'),
        ('2', '2 этаж'),
        ('3', '3 этаж'),
        ('mansard', 'Мансарда'),
    ]
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='floors')
    level = models.CharField(max_length=10, choices=FLOOR_CHOICES)

    class Meta:
        unique_together = ('block', 'level')

    def __str__(self):
        return f'{self.block.name} - {self.get_level_display()}'


class Plan(SiteAware):
    floor = models.OneToOneField(Floor, on_delete=models.CASCADE, related_name='plan')
    drawing = models.FileField(upload_to='plans/')
    description = models.CharField(max_length=255, blank=True)
    price_per_m2 = models.DecimalField("Цена за м²", max_digits=10, decimal_places=2, default=0)

    def get_price_per_m2(self):
        return self.price_per_m2

    def __str__(self):
        return f'Чертеж для {self.floor}'




class ProposalTemplate(models.Model):
    name = models.CharField("Название шаблона", max_length=200)
    content = models.TextField(
        "Текстовый шаблон (plain-text, с {placeholders})"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Шаблон предложения"
        verbose_name_plural = "Шаблоны предложений"

    def __str__(self):
        return self.name



class Proposal(models.Model):
    template = models.ForeignKey(
        ProposalTemplate,
        verbose_name="Шаблон",
        on_delete=models.PROTECT
    )
    application = models.ForeignKey(
        Application,
        verbose_name="Источник заявки",
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    block = models.ForeignKey(
        Block,
        on_delete=models.PROTECT
    )
    floor = models.ForeignKey(
        Floor,
        on_delete=models.PROTECT
    )
    area = models.DecimalField("Площадь, м²", max_digits=8, decimal_places=2)
    finish_level = models.CharField(
        "Отделка", max_length=50,
        choices=[('none','Без отделки'),('basic','Базовая'),('premium','Премиум')]
    )
    price_per_m2 = models.DecimalField(
        "Цена за м²", max_digits=10, decimal_places=2, default=0
    )
    total_price  = models.DecimalField(
        "Итоговая стоимость", max_digits=12, decimal_places=2, default=0
    )
    pdf_file     = models.FileField("PDF-документ", upload_to='proposals/', blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Коммерческое предложение"
        verbose_name_plural = "Коммерческие предложения"

    def __str__(self):
        return f"Предложение #{self.pk} — {self.block.name}, {self.floor.get_level_display()}"

    def save(self, *args, **kwargs):
        plan = self.floor.plan
        self.price_per_m2 = getattr(plan, 'price_per_m2', 0)
        self.total_price  = self.price_per_m2 * self.area
        super().save(*args, **kwargs)

    def generate_pdf(self):
        # 1) Контекст
        ctx = {
            'created_at':   self.created_at.strftime('%d.%m.%Y'),
            'block_name':   self.block.name,
            'floor':        self.floor.get_level_display(),
            'area':         self.area,
            'price_per_m2': self.price_per_m2,
            'total_price':  self.total_price,
            'client_section': (
                f"Контактные данные клиента:\n"
                f"Имя: {self.application.name}\n"
                f"Телефон: {self.application.phone}"
            ) if self.application else ''
        }

        logo_path      = os.path.join(settings.BASE_DIR, '../static', '../static', 'images', 'logo.png')
        brand_primary   = colors.HexColor('#052920')
        brand_secondary = colors.HexColor('#AF9578')

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20*mm, rightMargin=20*mm,
            topMargin=20*mm, bottomMargin=20*mm
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='ProposalTitle',
            parent=styles['Heading1'],
            fontName='DejaVuSans',
            fontSize=18,
            leading=22,
            alignment=1,  # по центру
            textColor=colors.white,
            backColor=brand_primary,
            spaceAfter=6*mm,
        ))
        normal = ParagraphStyle(
            'NormalBrand',
            parent=styles['Normal'],
            fontName='DejaVuSans',
            fontSize=11,
            leading=14,
            textColor=colors.black,
        )
        header_style = ParagraphStyle(
            'Header',
            parent=normal,
            fontName='DejaVuSans',
            fontSize=12,
            leading=15,
            textColor=brand_primary,
            spaceAfter=2*mm,
        )

        elements = []

        if os.path.exists(logo_path):
            img = Image(logo_path, height=20*mm, hAlign='LEFT')
            elements.append(img)
        elements.append(Paragraph("Коммерческое предложение", styles['ProposalTitle']))


        elements.append(Paragraph(f"<font color='{brand_secondary.hexval()}'>Дата: {ctx['created_at']}</font>", normal))
        elements.append(Spacer(1, 6*mm))

        elements.append(Paragraph("Объект:", header_style))
        elements.append(Paragraph(f"Блок: {ctx['block_name']}, этаж: {ctx['floor']}", normal))
        elements.append(Spacer(1, 6*mm))

        data = [
            ['Параметр', 'Значение'],
            ['Площадь, м²', f"{ctx['area']}"],
            ['Цена за м²', f"{ctx['price_per_m2']} ₸"],
            ['Итоговая стоимость', f"{ctx['total_price']} ₸"],
        ]
        table = Table(data, colWidths=[60*mm, 60*mm])
        table.setStyle(TableStyle([
            ('FONTNAME',    (0,0), (-1,-1), 'DejaVuSans'),
            ('FONTSIZE',    (0,0), (-1,-1), 11),
            ('BACKGROUND',  (0,0), (-1,0), brand_secondary),
            ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
            ('ALIGN',       (0,0), (-1,0), 'CENTER'),
            ('GRID',        (0,0), (-1,-1), 0.5, colors.grey),
            ('ALIGN',       (1,1), (1,-1), 'RIGHT'),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 6*mm))

        if ctx['client_section']:
            elements.append(Paragraph("Контактные данные клиента:", header_style))
            for line in ctx['client_section'].splitlines():
                elements.append(Paragraph(line, normal))
            elements.append(Spacer(1, 6*mm))

        elements.append(Paragraph("Условия оплаты: 50% предоплата, 50% — при сдаче объекта.", normal))
        elements.append(Paragraph("Срок сдачи: согласовывается дополнительно.", normal))
        elements.append(Spacer(1, 6*mm))

        elements.append(Paragraph("Спасибо за внимание!", normal))
        elements.append(Paragraph("С уважением, команда Seneca Partners", normal))

        doc.build(elements)
        buffer.seek(0)
        self.pdf_file.save(f'proposal_{self.pk}.pdf', ContentFile(buffer.read()), save=False)
        buffer.close()
        super().save(update_fields=['pdf_file'])