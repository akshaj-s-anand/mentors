# Generated by Django 4.2.8 on 2024-01-01 12:28

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mentorapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentors',
            name='pub_date',
            field=models.DateTimeField(default=datetime.datetime.now, verbose_name='date published'),
        ),
    ]