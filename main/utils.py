import json

from django.core import serializers
from pathlib import Path
from os import path


def user_exists(request):
    return request.session.get('user_id') is not None


def delete_past_session(request):
    if request.session.get('user_id') is not None:
        del request.session['user_id']


def load_view_template(name):
    root = Path(__file__).resolve().parent.parent
    template = path.join(root, 'main\\templates\\main\\' + name)
    with open(template, 'r') as file:
        raw = file.read()
        return raw.replace('\n', '')  # replacing white characters for main script


def serialize_model(model, **kwargs):
    query_set = model.objects.filter(**kwargs) if kwargs != dict() else model.objects.all()
    raw = serializers.serialize('json', query_set)
    return json.loads(raw)
