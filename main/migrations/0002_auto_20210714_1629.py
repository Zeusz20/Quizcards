# Generated by Django 3.2.4 on 2021-07-14 14:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='card',
            name='definition_image',
            field=models.FileField(blank=True, null=True, upload_to='static/media'),
        ),
        migrations.AlterField(
            model_name='card',
            name='term_image',
            field=models.FileField(blank=True, null=True, upload_to='static/media/'),
        ),
    ]