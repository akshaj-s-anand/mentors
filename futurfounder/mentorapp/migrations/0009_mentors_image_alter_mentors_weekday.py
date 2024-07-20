# Generated by Django 4.2.3 on 2024-01-02 06:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mentorapp', '0008_specialization_delete_expertise'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentors',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='mentor_images/'),
        ),
        migrations.AlterField(
            model_name='mentors',
            name='weekday',
            field=models.CharField(blank=True, choices=[('monday', 'Monday'), ('tuesday', 'Tuesday'), ('wednesday', 'Wednesday'), ('thursday', 'Thursday'), ('friday', 'Friday'), ('saturday', 'Saturday'), ('sunday', 'Sunday')], max_length=10, null=True),
        ),
    ]