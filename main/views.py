import json

from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import View
from datetime import date
from uuid import uuid4
from . import authentication as auth, utils
from .models import *


# Create your views here.


class IndexView(View):
    template_name = 'main/index.html'

    def get(self, request):
        utils.delete_past_session(request)

        if request.GET.get('view') is None:
            return redirect('/?view=login')

        context = {
            'form': request.GET['view'],
            'index': True,  # this changes the header depending on if the user is authenticated
        }

        return render(request, self.template_name, context)

    def post(self, request):
        if request.GET['view'] == 'register':
            self._handle_registration(request)
            return redirect('/?view=login')
        else:
            self._handle_login(request)
            return redirect('/user')

    def _handle_login(self, request):
        if auth.validate_login(request):
            user = User.objects.get(username=request.POST['username'])
            request.session['user_id'] = user.pk    # create session for user

    def _handle_registration(self, request):
        if auth.validate_registration(request):
            messages.success(request, 'Registration successful!')


class UserView(View):
    template_name = 'main/user.html'

    def get(self, request):
        if not utils.user_exists(request):
            return redirect('/?view=login')

        user_id = request.session.get('user_id')
        User.objects.filter(pk=user_id).update(last_login=date.today())

        context = self._get_user_data(user_id)
        return render(request, self.template_name, context)

    def post(self, request):
        if request.POST.get('delete'):
            self._handle_delete(request)    # user deletes a deck
            return redirect('/user')
        else:
            self._handle_password_change(request)
            return redirect('/user')

    def _get_user_data(self, user_id):
        user = User.objects.get(pk=user_id)

        return {
            'username': user.username,
            'date_created': user.date_created,
            'decks': utils.serialize_model(Deck, user=user),
            'template': utils.load_view_template('deck_view_template.html'),
        }

    def _handle_delete(self, request):
        deck_id = request.POST['delete']
        deck = Deck.objects.get(pk=deck_id)
        name = deck.name
        deck.delete()
        messages.success(request, 'Deck "{}" was successfully deleted.'.format(name))

    def _handle_password_change(self, request):
        if auth.change_password(request):
            messages.success(request, 'Password changed successfully.')


class EditorView(View):
    template_name = 'main/editor.html'

    def get(self, request):
        if not utils.user_exists(request):
            return redirect('/?view=login')

        if request.GET.get('uuid') is not None:
            context = self._load_deck(request)
            return render(request, self.template_name, context)
        else:
            context = self._create_deck()
            return render(request, self.template_name, context)

    def post(self, request):
        old = json.loads(request.POST['old']) if request.POST.get('old') else None
        new = json.loads(request.POST['deck'])

        if old is None:
            self._save_deck(request, new)
            return redirect('/user')
        else:
            self._update_deck(request, old, new)
            return redirect('/user')

    def _create_deck(self):
        return {
            'num_of_cards': list(range(1)),
            'template': utils.load_view_template('card_view_template.html'),
        }

    def _load_deck(self, request):
        uuid = request.GET['uuid']
        deck = Deck.objects.get(uuid=request.GET['uuid'])
        cards = list(Card.objects.filter(deck=deck))

        return {
            'deck': utils.serialize_model(Deck, uuid=uuid)[0],
            'cards': utils.serialize_model(Card, deck=deck),
            'num_of_cards': range(len(cards)),
            'template': utils.load_view_template('card_view_template.html'),
        }

    def _save_deck(self, request, data):
        user = User.objects.get(pk=request.session['user_id'])
        data['uuid'] = uuid4()

        Deck(
            user=user,
            name=data['name'],
            description=data['description'],
            uuid=data['uuid'],
            date_created=date.today(),
            last_modified=date.today()
        ).save()

        self._save_cards(request, data)
        messages.success(request, 'Deck "{}" created successfully.'.format(data['name']))

    def _update_deck(self, request, old, new):
        deck = Deck.objects.get(uuid=old['uuid'])
        cards = list(Card.objects.filter(deck=deck))
        cards = list(map(lambda card: utils.serialize_model(Card, pk=card.pk).pop(), cards))


    def _save_cards(self, request, data):
        deck = Deck.objects.get(uuid=data['uuid'])
        term_images = request.FILES.getlist('term-image')
        definition_images = request.FILES.getlist('definition-images')

        for card in data['cards']:
            term_image = term_images.pop(0) if card['term_image'] != '' else None
            definition_image = definition_images.pop(0) if card['definition_image'] != '' else None

            Card(
                deck=deck,
                term=card['term'],
                term_image=term_image,
                definition=card['definition'],
                definition_image=definition_image
            ).save()

    def _update_cards(self, request, old, new):
        pass


def editor(request):
    if not utils.user_exists(request):
        return redirect('/?view=login')

    parent_user = User.objects.get(pk=request.session['user_id'])

    # load deck
    if request.method == 'GET' and request.GET.get('uuid') is not None:
        uuid = request.GET['uuid']
        deck = Deck.objects.get(uuid=request.GET['uuid'])
        cards = list(Card.objects.filter(deck=deck))

        context = {
            'deck': utils.serialize_model(Deck, uuid=uuid)[0],
            'cards': utils.serialize_model(Card, deck=deck),
            'num_of_cards': range(len(cards)),
            'template': utils.load_view_template('card_view_template.html'),
        }

        return render(request, 'main/editor.html', context)

    # save deck
    if request.method == 'POST':

        original = None
        if request.POST.get('original') is not None:
            original = json.loads(request.POST['original'])

        data = json.loads(request.POST['deck'])

        deck = Deck(
            user=parent_user,
            name=data['name'],
            description=data['description'],
            uuid=data['uuid'] if data['uuid'] != '' else uuid4(),
            date_created=date.today(),
            last_modified=date.today()
        )
        deck.save()

        term_images = request.FILES.getlist('term-image')
        definition_images = request.FILES.getlist('definition-images')

        for card in data['cards']:
            term_image = term_images.pop(0) if card['term_image'] != '' else None
            definition_image = definition_images.pop(0) if card['definition_image'] != '' else None

            Card(
                deck=deck,
                term=card['term'],
                term_image=term_image,
                definition=card['definition'],
                definition_image=definition_image
            ).save()

        messages.success(request, 'Deck {} created successfully.'.format(data['name']))
        return redirect('/user')

    context = {
        'num_of_cards': list(range(1)),
        'template': utils.load_view_template('card_view_template.html'),
    }

    return render(request, 'main/editor.html', context)
