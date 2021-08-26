import django.db.models.deletion

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Deck',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128)),
                ('description', models.CharField(default='', max_length=512, null=True)),
                ('uuid', models.UUIDField()),
                ('date_created', models.DateField()),
                ('last_modified', models.DateField()),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('term', models.CharField(max_length=512)),
                ('term_image', models.FileField(blank=True, null=True, upload_to=settings.MEDIA_ROOT)),
                ('definition', models.CharField(max_length=512)),
                ('definition_image', models.FileField(blank=True, null=True, upload_to=settings.MEDIA_ROOT)),
                ('deck', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.deck')),
            ],
        ),
    ]
