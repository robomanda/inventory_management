# Generated by Django 5.1.5 on 2025-01-29 13:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_ownerdata'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownerdata',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='logos/'),
        ),
    ]
