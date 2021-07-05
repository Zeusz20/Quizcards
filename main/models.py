from django.db import models

# Create your models here.

DEFAULT_LENGTH = 256
CARD_STR_LENGTH = 1024


class User(models.Model):
    username = models.CharField(max_length=DEFAULT_LENGTH)
    email = models.EmailField()
    password = models.CharField(max_length=DEFAULT_LENGTH)
    date_created = models.DateField()
    last_login = models.DateField()


class Deck(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=DEFAULT_LENGTH)
    uuid = models.UUIDField()
    date_created = models.DateField(auto_now_add=True)
    last_modified = models.DateField()


class Card(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE)
    term_image = models.CharField(max_length=DEFAULT_LENGTH)
    term = models.CharField(max_length=CARD_STR_LENGTH)
    definition_image = models.CharField(max_length=DEFAULT_LENGTH)
    definition = models.CharField(max_length=CARD_STR_LENGTH)
