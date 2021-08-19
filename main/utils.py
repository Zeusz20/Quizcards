from django.core.serializers import serialize as django_serialize
from django.db.models import Q
from json import loads as json_loads
from os.path import basename
from .models import Deck

USER_VIEW_PAGE_SIZE = 7
SEARCH_VIEW_PAGE_SIZE = 10


def user_exists(request):
    return request.session.get('user_id') is not None


def session_clean_up(view, request):
    for key in dict(request.session).keys():
        if key not in view.session_keys:
            del request.session[key]


def serialize(query):
    is_iterable = hasattr(query, '__iter__')
    queryset = query if is_iterable else [query]
    raw = django_serialize('json', queryset)
    serialized = json_loads(raw)

    # remap card image names so client cannot see full server path
    for model in serialized:
        if model['model'] == 'main.card':
            model['fields']['term_image'] = basename(model['fields']['term_image'])
            model['fields']['definition_image'] = basename(model['fields']['definition_image'])

    return serialized if is_iterable else serialized.pop()


def random_string(length):
    from random import choice
    from string import ascii_letters, digits
    return ''.join(choice(ascii_letters + digits) for _ in range(length))


def validate_datetime(day, hour, minute):
    if not 1 <= day <= 7:
        raise ValueError(day)
    if not 0 <= hour <= 23:
        raise ValueError(hour)
    if not 0 <= minute <= 59:
        raise ValueError(minute)


def get_decks_from_query(user=None, query='', local=False):
    if user is None:
        # non logged in user's global search
        return Deck.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by

    if query == '':
        # logged in user's deck pagination
        return Deck.objects.filter(user=user)

    if local:
        # logged in user's local search
        return Deck.objects.filter(
            Q(user=user),
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        # logged in user's global search
        return Deck.objects.filter(
            ~Q(user=user),
            Q(name__icontains=query) | Q(description__icontains=query)
        )
