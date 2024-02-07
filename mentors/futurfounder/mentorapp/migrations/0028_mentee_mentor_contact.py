# Generated by Django 4.2.3 on 2024-01-09 12:28

from django.db import migrations, models
import mentorapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('mentorapp', '0027_mentors_contact'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentee',
            name='mentor_contact',
            field=models.CharField(default='Contact number not found 😔', max_length=15, validators=[mentorapp.models.validate_phone_number]),
        ),
    ]