from django.conf import settings
from django.db.models import *
from django.db.models.fields.files import FieldFile
from os.path import basename, join

# used as default user model
from django.contrib.auth.models import User

SHORT_LENGTH = 128
LONG_LENGTH = 512


class ImageField(FileField):
    """Used by Card models for easier access to html image alt attribute."""

    class FieldImage(FieldFile):
        @property
        def alt(self):
            return basename(self.name)

    attr_class = FieldImage


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
    term_image = ImageField(upload_to=settings.MEDIA_ROOT, null=True, blank=True)
    definition = CharField(max_length=LONG_LENGTH)
    definition_image = ImageField(upload_to=settings.MEDIA_ROOT, null=True, blank=True)
