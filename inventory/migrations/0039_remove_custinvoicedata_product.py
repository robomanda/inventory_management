# Generated by Django 5.1.5 on 2025-02-04 19:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0038_remove_invoicedetail_customer_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='custinvoicedata',
            name='product',
        ),
    ]
