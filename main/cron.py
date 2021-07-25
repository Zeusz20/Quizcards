from django.conf import settings
from os import listdir
from .models import Card


def file_cleanup():
    # TODO
    cards = list(Card.objects.all())
    images = list(map(lambda card: (card.term_image, card.definition_image), cards))
    term_images, definition_images = zip(*images)
    print(term_images, definition_images)

    for file in listdir(settings.MEDIA_ROOT):
        pass
