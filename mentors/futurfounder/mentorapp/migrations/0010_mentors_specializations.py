# Generated by Django 4.2.3 on 2024-01-02 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mentorapp', '0009_mentors_image_alter_mentors_weekday'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentors',
            name='specializations',
            field=models.ManyToManyField(blank=True, related_name='mentors', to='mentorapp.specialization'),
        ),
    ]
