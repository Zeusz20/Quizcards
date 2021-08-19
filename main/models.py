from django.conf import settings
from django.db.models import *
from .utils import get_image_url

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
    description = CharField(max_length=LENGTH, null=True, default='')
    uuid = UUIDField()
    date_created = DateField()
    last_modified = DateField()


class Card(Model):
    deck = ForeignKey(Deck, on_delete=CASCADE)
    term = CharField(max_length=LENGTH)
    term_image = FileField(upload_to=settings.MEDIA_ROOT, null=True, blank=True)
    definition = CharField(max_length=LENGTH)
    definition_image = FileField(upload_to=settings.MEDIA_ROOT, null=True, blank=True)

    def term_image_url(self):
        return get_image_url(self.term_image.name) if self.term_image else ''

    def definition_image_url(self):
        return get_image_url(self.definition_image.name) if self.definition_image else ''
