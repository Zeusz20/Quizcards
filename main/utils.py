import json

from django.core import serializers
from os import path
from pathlib import Path


def user_exists(request):
    return request.session.get('user_id') is not None


def delete_past_session(request):
    if request.session.get('user_id') is not None:
        del request.session['user_id']


def load_view_template(name):
    root = Path(__file__).resolve().parent.parent
    parent = path.join('main', 'templates', 'main')
    template = path.join(root, parent, name)
    with open(template, 'r') as file:
        raw = file.read()
        return raw.replace('\n', '')  # replace new line characters for js script


def serialize_model(model, **kwargs):
    query_set = model.objects.filter(**kwargs) if kwargs != {} else model.objects.all()
    raw = serializers.serialize('json', query_set)
    return json.loads(raw)
