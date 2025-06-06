# Generated by Django 5.2.1 on 2025-05-09 12:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('phone', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Block',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1)),
            ],
        ),
        migrations.CreateModel(
            name='Photo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='photos/')),
                ('caption', models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='ProposalTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название шаблона')),
                ('content', models.TextField(verbose_name='Текстовый шаблон (plain-text, с {placeholders})')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Шаблон предложения',
                'verbose_name_plural': 'Шаблоны предложений',
            },
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('youtube_link', models.URLField()),
                ('description', models.TextField(blank=True)),
                ('year', models.CharField(max_length=4)),
                ('month', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Floor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.CharField(choices=[('1', '1 этаж'), ('2', '2 этаж'), ('3', '3 этаж'), ('mansard', 'Мансарда')], max_length=10)),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='floors', to='seneca.block')),
            ],
            options={
                'unique_together': {('block', 'level')},
            },
        ),
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('drawing', models.FileField(upload_to='plans/')),
                ('description', models.CharField(blank=True, max_length=255)),
                ('floor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='plan', to='seneca.floor')),
            ],
        ),
        migrations.CreateModel(
            name='Proposal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('area', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Площадь, м²')),
                ('finish_level', models.CharField(choices=[('none', 'Без отделки'), ('basic', 'Базовая'), ('premium', 'Премиум')], max_length=50, verbose_name='Отделка')),
                ('price_per_m2', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Цена за м²')),
                ('total_price', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='Итоговая стоимость')),
                ('pdf_file', models.FileField(blank=True, upload_to='proposals/', verbose_name='PDF-документ')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('application', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='seneca.application', verbose_name='Источник заявки')),
                ('block', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='seneca.block')),
                ('floor', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='seneca.floor')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='seneca.proposaltemplate', verbose_name='Шаблон')),
            ],
            options={
                'verbose_name': 'Коммерческое предложение',
                'verbose_name_plural': 'Коммерческие предложения',
            },
        ),
    ]
