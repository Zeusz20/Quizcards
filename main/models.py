from django.conf import settings
from django.db.models import *

LENGTH = 512


class User(Model):
    username = CharField(max_length=LENGTH)
    email = EmailField()
    password = CharField(max_length=LENGTH)
    date_created = DateField()
    last_login = DateField()


class Deck(Model):
    user = ForeignKey(User, on_delete=SET_NULL, null=True)
    name = CharField(max_length=LENGTH)
    description = CharField(max_length=LENGTH, null=True)
    uuid = UUIDField()
    date_created = DateField()
    last_modified = DateField()


class Card(Model):
    deck = ForeignKey(Deck, on_delete=CASCADE)
    term = CharField(max_length=LENGTH)
    term_image = FileField(upload_to=settings.MEDIA_ROOT, null=True, blank=True)
    definition = CharField(max_length=LENGTH)
    definition_image = FileField(upload_to=settings.MEDIA_ROOT, null=True, blank=True)
