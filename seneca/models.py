from django.db import models


#Dilnaz
class Photo(models.Model):
    image = models.ImageField(upload_to='photos/')
    caption = models.CharField(max_length=255, blank=True)

    def __str__\
                    (self):
        return self.caption or "Фото без подписи"

    class Meta:
        verbose_name = "Фото"
        verbose_name_plural = "Фотографии"

class Video(models.Model):
    youtube_link = models.URLField()
    description = models.TextField(blank=True)
    year = models.CharField(max_length=4)
    month = models.CharField(max_length=20)

    def __str__(self):
        return self.youtube_link

    class Meta:
        verbose_name = "Видео"
        verbose_name_plural = "Видеозаписи"

class Application(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f'{self.name} - {self.phone}'

    class Meta:
        verbose_name = "Заявка"
        verbose_name_plural = "Заявки"



class Block(models.Model):
    name = models.CharField(max_length=1)

    def __str__(self):
        return f'Блок {self.name}'

    class Meta:
        verbose_name = "Блок"
        verbose_name_plural = "Блоки"


class Floor(models.Model):
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
        verbose_name = "Этаж"
        verbose_name_plural = "Этажи"


    def __str__(self):
        return f'{self.block.name} - {self.get_level_display()}'


class Plan(models.Model):
    floor = models.OneToOneField(Floor, on_delete=models.CASCADE, related_name='plan')
    drawing = models.FileField(upload_to='plans/')
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f'Чертеж для {self.floor}'

    class Meta:
        verbose_name = "План"
        verbose_name_plural = "Планы"


class ProposalTemplate(models.Model):
    name = models.CharField("Название шаблона", max_length=200)
    content = models.TextField(
        "Текстовый шаблон (plain-text, с {placeholders})"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Шаблон предложения"
        verbose_name_plural = "Шаблоны предложений"

    def _str_(self):
        return self.name






class Proposal(models.Model):
    template = models.ForeignKey(ProposalTemplate, verbose_name="Шаблон", on_delete=models.PROTECT)
    application = models.ForeignKey(Application, verbose_name="Источник заявки", on_delete=models.SET_NULL, null=True, blank=True)
    block = models.ForeignKey(Block, on_delete=models.PROTECT)
    floor = models.ForeignKey(Floor, on_delete=models.PROTECT)
    area = models.DecimalField("Площадь, м²", max_digits=8, decimal_places=2)
    finish_level = models.CharField("Отделка", max_length=50,
        choices=[('none','Без отделки'),('basic','Базовая'),('premium','Премиум')]
    )
    price_per_m2 = models.DecimalField("Цена за м²", max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField("Итоговая стоимость", max_digits=12, decimal_places=2, default=0)
    pdf_file = models.FileField("PDF-документ", upload_to='proposals/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = "Коммерческое предложение"
        verbose_name_plural = "Коммерческие предложения"

    def _str_(self):
        return f"Предложение #{self.pk} — {self.block.name}, {self.floor.get_level_display()}"
