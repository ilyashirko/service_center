# Generated by Django 4.0.4 on 2022-05-11 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_message_alter_request_created_at_request_messages'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='is_master',
            field=models.BooleanField(default=None, null=True, verbose_name='Сообщение от мастера'),
        ),
    ]
