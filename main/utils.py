import json

from django.core import serializers
from django.db.models import Q
from random import choice
from string import ascii_letters, digits
from .models import Deck

USER_VIEW_PAGE_SIZE = 7
SEARCH_VIEW_PAGE_SIZE = 10


def user_exists(request):
    return request.session.get('user_id') is not None


def clear_session(view, request):
    from .views import CheckoutView, EditorView, IndexView, SearchView, StudyView, UserView

    allowed_keys = ['user_id']

    if isinstance(view, UserView):
        allowed_keys += ['local_search']
    elif isinstance(view, EditorView):
        allowed_keys += ['uuid']
    elif isinstance(view, SearchView):
        allowed_keys += ['anonym', 'global_search']
    elif isinstance(view, StudyView):
        allowed_keys += ['anonym', 'uuid']
    elif isinstance(view, CheckoutView):
        allowed_keys += ['checkout']
    elif isinstance(view, IndexView):
        allowed_keys = ['anonym']   # only anonymous users

    keys_to_remove = list()
    for key in request.session.keys():
        if key not in allowed_keys:
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del request.session[key]


def clear_editor_session(request):
    if request.session.get('uuid'):
        del request.session['uuid']


def serialize(query):
    is_iterable = hasattr(query, '__iter__')
    queryset = query if is_iterable else [query]
    raw = serializers.serialize('json', queryset)
    serialized = json.loads(raw)
    return serialized if is_iterable else serialized.pop()


def random_string(length):
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
        )

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
