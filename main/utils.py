import json

from django.core import serializers
from .models import *
from pathlib import Path
from os import path


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


def get_card_list(request):
    terms = request.POST.getlist('terms[]')
    term_indexes = request.POST.getlist('term-indexes[]')
    term_images = request.FILES.getlist('term-images[]')
    definitions = request.POST.getlist('definitions[]')
    definition_indexes = request.POST.getlist('definition-indexes[]')
    definition_images = request.FILES.getlist('definition-images[]')
    data_length = len(terms)

    cards = list()
    term_image_index = 0
    definition_image_index = 0

    for i in range(data_length):
        card = dict()
        card['term'] = terms[i]
        card['definition'] = definitions[i]

        for index in range(len(term_indexes)):
            if term_indexes[index] != '' and index == i:
                card['term_image'] = term_images[term_image_index]
                term_image_index += 1

        for index in range(len(definition_indexes)):
            if definition_indexes[index] != '' and index == i:
                card['definition_image'] = definition_images[definition_image_index]
                definition_image_index += 1

        cards.append(card)

    return cards


def get_deck_json(deck):
    deck_json = {
        'name': deck.name,
        'description': deck.description,
        'uuid': deck.uuid,
        'cards': list()
    }

    for card_obj in list(Card.objects.filter(deck=deck)):
        deck_json['cards'].append({
            'term': card_obj.term,
            'term_image': card_obj.term_image != '',    # has term image
            'definition': card_obj.definition,
            'definition_image': card_obj.definition_image != '',    # has definition image
        })

    return deck_json
