import json

from django.conf import settings
from django.core import serializers
from os import path


def user_exists(request):
    return request.session.get('user_id') is not None


def delete_past_session(request):
    if request.session.get('user_id') is not None:
        del request.session['user_id']


def load_view_template(name):
    parent = path.join('main', 'templates')
    template = path.join(settings.BASE_DIR, parent, name)
    with open(template, 'r') as file:
        raw = file.read()
        return raw.replace('\n', '')  # replace new line characters for js script


def serialize(query):
    is_iterable = hasattr(query, '__iter__')
    queryset = query if is_iterable else [query]
    raw = serializers.serialize('json', queryset)
    serialized = json.loads(raw)
    return serialized if is_iterable else serialized.pop()


def validate_datetime(day, hour, minute):
    if not 1 <= day <= 7:
        raise ValueError(day)

    if not 0 <= hour <= 23:
        raise ValueError(hour)

    if not 0 <= minute <= 59:
        raise ValueError(minute)
