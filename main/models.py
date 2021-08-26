from django.conf import settings
from django.db.models import *
from os.path import basename
from .utils import get_image_url

# used as default user model
from django.contrib.auth.models import User

SHORT_LENGTH = 128
LONG_LENGTH = 512


class Deck(Model):
    user = ForeignKey(User, on_delete=SET_NULL, null=True)
    name = CharField(max_length=SHORT_LENGTH)
    description = CharField(max_length=LONG_LENGTH, null=True, default='')
    uuid = UUIDField()
    date_created = DateField()
    last_modified = DateField()


class Card(Model):
    deck = ForeignKey(Deck, on_delete=CASCADE)
    term = CharField(max_length=LONG_LENGTH)
    term_image = FileField(upload_to=settings.MEDIA_ROOT, null=True, blank=True)
    definition = CharField(max_length=LONG_LENGTH)
    definition_image = FileField(upload_to=settings.MEDIA_ROOT, null=True, blank=True)

    def term_image_alt(self):
        return basename(self.term_image.name)

    def definition_image_alt(self):
        return basename(self.definition_image.name)

    def term_image_url(self):
        return get_image_url(self.term_image.name)

    def definition_image_url(self):
        return get_image_url(self.definition_image.name)
