# Generated by Django 3.2.4 on 2021-06-29 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_alter_user_date_created'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='last_login',
        ),
        migrations.AlterField(
            model_name='user',
            name='date_created',
            field=models.DateField(auto_now_add=True),
        ),
    ]
