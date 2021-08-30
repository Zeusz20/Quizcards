from django.template import Library
from django.utils.html import html_safe
from django.forms.widgets import Widget

register = Library()

FACEBOOK_SHARE_URL = 'https://www.facebook.com/sharer/sharer.php?u='
FACEBOOK_ICON_SRC = 'https://cdn.icon-icons.com/icons2/836/PNG/512/Facebook_icon-icons.com_66805.png'
TWITTER_SHARE_URL = 'https://twitter.com/intent/tweet?text='
TWITTER_ICON_SRC = 'https://cdn.icon-icons.com/icons2/555/PNG/512/twitter_icon-icons.com_53611.png'


@register.simple_tag(takes_context=True)
def facebook(context, uuid, **kwargs):
    request = None
    for dictionary in context:
        if 'request' in dictionary.keys():
            request = dictionary['request']
            break

    share_url = '/'.join([request.get_host(), 'flashcards', uuid])
    return f'<a href={FACEBOOK_SHARE_URL}{share_url}><img src={FACEBOOK_ICON_SRC}></a>'


class SocialWidget:
    def __init__(self, request, uuid):
        pass