# Generated by Django 5.1.5 on 2025-01-31 19:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0020_custinvoicedata_desc_alter_custinvoicedata_imi'),
    ]

    operations = [
        migrations.AlterField(
            model_name='custinvoicedata',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.customerdata'),
        ),
    ]
