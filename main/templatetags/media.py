from django.conf import settings
from django.template import Library
from os.path import basename

register = Library()


@register.simple_tag
def media(image):
    return settings.MEDIA_URL + basename(image.name)
