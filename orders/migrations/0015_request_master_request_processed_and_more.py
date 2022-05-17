# Generated by Django 4.0.4 on 2022-05-17 09:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0014_rename_is_actual_support_processed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='master',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='requests', to='orders.master'),
        ),
        migrations.AddField(
            model_name='request',
            name='processed',
            field=models.BooleanField(default=False, verbose_name='Заявка отработана'),
        ),
        migrations.AlterField(
            model_name='support',
            name='processed',
            field=models.BooleanField(verbose_name='Заявка отработана'),
        ),
    ]