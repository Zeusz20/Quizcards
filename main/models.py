from django.db import models

# Create your models here.

LENGTH = 512


class User(models.Model):
    username = models.CharField(max_length=LENGTH)
    email = models.EmailField()
    password = models.CharField(max_length=LENGTH)
    date_created = models.DateField()
    last_login = models.DateField()


class Deck(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=LENGTH)
    description = models.CharField(max_length=LENGTH, null=True)
    uuid = models.UUIDField()
    date_created = models.DateField()
    last_modified = models.DateField()


class Card(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    term = models.CharField(max_length=LENGTH)
    term_image = models.FileField(upload_to='static/media/', null=True, blank=True)
    definition = models.CharField(max_length=LENGTH)
    definition_image = models.FileField(upload_to='static/media', null=True, blank=True)
