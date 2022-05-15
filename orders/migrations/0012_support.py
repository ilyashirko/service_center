# Generated by Django 4.0.4 on 2022-05-15 15:17

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0011_alter_telegramid_telegram_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Support',
            fields=[
                ('uuid', models.CharField(default=uuid.uuid1, editable=False, max_length=36, primary_key=True, serialize=False, unique=True, validators=[django.core.validators.MinLengthValidator(36)], verbose_name='id')),
                ('text', models.CharField(max_length=1000, verbose_name='Сообщение')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Отправлено')),
                ('is_actual', models.BooleanField(verbose_name='Заявка актуальна')),
                ('telegram_id', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='support', to='orders.telegramid', verbose_name='Telegram ID')),
            ],
        ),
    ]
