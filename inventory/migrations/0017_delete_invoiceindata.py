# Generated by Django 5.1.5 on 2025-01-31 13:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0016_rename_invoicedata_invoiceindata'),
    ]

    operations = [
        migrations.DeleteModel(
            name='InvoiceinData',
        ),
    ]
