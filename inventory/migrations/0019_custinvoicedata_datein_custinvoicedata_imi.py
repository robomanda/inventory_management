# Generated by Django 5.1.5 on 2025-01-31 14:34

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0018_custinvoicedata'),
    ]

    operations = [
        migrations.AddField(
            model_name='custinvoicedata',
            name='datein',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='custinvoicedata',
            name='imi',
            field=models.CharField(default=0, max_length=50),
        ),
    ]
