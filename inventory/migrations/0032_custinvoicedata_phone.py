# Generated by Django 5.1.5 on 2025-02-04 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0031_remove_invoicedetail_custid'),
    ]

    operations = [
        migrations.AddField(
            model_name='custinvoicedata',
            name='phone',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
