# Generated by Django 5.1.5 on 2025-01-29 14:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_ownerdata_logo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ownerdata',
            name='logo',
        ),
    ]
