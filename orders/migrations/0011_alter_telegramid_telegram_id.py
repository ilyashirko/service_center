# Generated by Django 4.0.4 on 2022-05-13 08:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0010_alter_message_request'),
    ]

    operations = [
        migrations.AlterField(
            model_name='telegramid',
            name='telegram_id',
            field=models.SmallIntegerField(unique=True, verbose_name='Telegram ID'),
        ),
    ]
