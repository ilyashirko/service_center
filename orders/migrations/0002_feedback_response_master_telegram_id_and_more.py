# Generated by Django 4.0.4 on 2022-05-11 11:50

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feedback',
            name='response',
            field=models.TextField(blank=True, max_length=500, null=True, verbose_name='Ответ от администратора'),
        ),
        migrations.AddField(
            model_name='master',
            name='telegram_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='master', to='orders.telegramid', verbose_name='Telegram ID'),
        ),
        migrations.AlterField(
            model_name='devicetype',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='feedback',
            name='text',
            field=models.TextField(max_length=500, verbose_name='Текст отзыва'),
        ),
        migrations.AlterField(
            model_name='telegramid',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.CreateModel(
            name='Request',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid1, editable=False, max_length=36, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.MinLengthValidator(36)], verbose_name='id')),
                ('message', models.CharField(max_length=1000, verbose_name='Сообщение от пользователя')),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, verbose_name='Номер телефона')),
                ('user_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='TG username')),
                ('first_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='TG first name')),
                ('created_at', models.DateField(auto_now_add=True, verbose_name='Дата отзыва')),
                ('user_telegram_id', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='orders', to='orders.telegramid', verbose_name='Telegram ID')),
            ],
        ),
    ]
