# Generated by Django 5.1.5 on 2025-02-06 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0040_alter_custinvoicedata_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='custinvoicedata',
            name='total_sales',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
