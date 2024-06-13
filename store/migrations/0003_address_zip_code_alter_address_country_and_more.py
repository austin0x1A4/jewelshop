# Generated by Django 5.0.6 on 2024-06-12 04:59

import django_countries.fields
import localflavor.us.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_remove_address_locality_alter_address_address_line1_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='address',
            name='zip_code',
            field=localflavor.us.models.USZipCodeField(default='0000', max_length=10, verbose_name='ZIP Code'),
        ),
        migrations.AlterField(
            model_name='address',
            name='country',
            field=django_countries.fields.CountryField(default='US', max_length=2, verbose_name='Country'),
        ),
        migrations.AlterField(
            model_name='address',
            name='state',
            field=localflavor.us.models.USStateField(max_length=2, verbose_name='State'),
        ),
    ]
