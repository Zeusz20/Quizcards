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

    if is_iterable:
        raw = serializers.serialize('json', query)
    else:
        raw = serializers.serialize('json', [query])

    serialized = json.loads(raw)

    # remap filenames of the respective image files,
    # so the client does not receive the full path of the file
    if serialized != [] and serialized[0]['model'] == 'main.card':
        for card in serialized:
            card['fields']['term_image'] = path.basename(card['fields']['term_image'])
            card['fields']['definition_image'] = path.basename(card['fields']['definition_image'])

    return serialized if is_iterable else serialized.pop()
