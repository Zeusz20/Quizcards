import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from datetime import date
from . import authentication as auth, utils
from .models import *


class IndexView(View):
    template_name = 'main/index.html'

    def get(self, request):

        if request.GET.get('logout') == '':
            utils.delete_past_session(request)

        if utils.user_exists(request):
            return redirect('/user')

        if request.GET.get('view') is None:
            return redirect('/?view=login')

        context = {
            'form': request.GET['view'],
            'user': False,  # this changes the header depending on if the user is authenticated
        }

        return render(request, self.template_name, context)

    def post(self, request):
        if request.GET['view'] == 'register':
            self._handle_registration(request)
            return redirect('/')
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
    dynamic_template = utils.load_view_template('main/deck_view.html')

    def get(self, request):
        if not utils.user_exists(request):
            return redirect('/')

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
        decks = Deck.objects.filter(user=user)

        return {
            'username': user.username,
            'date_created': user.date_created,
            'decks': utils.serialize(decks),
            'template': self.dynamic_template,
        }

    def _handle_delete(self, request):
        deck_id = request.POST['delete']
        deck = Deck.objects.get(pk=deck_id)
        name = deck.name
        deck.delete()
        messages.success(request, f'Deck "{name}" was successfully deleted.')

    def _handle_password_change(self, request):
        if auth.change_password(request):
            messages.success(request, 'Password changed successfully.')


class EditorView(View):
    template_name = 'main/editor.html'
    dynamic_template = utils.load_view_template('main/base_card_view.html')

    def get(self, request):
        if not utils.user_exists(request):
            return redirect('/')

        if request.GET.get('uuid'):
            context = self._load_deck(request)
        else:
            context = self._create_deck()

        return render(request, self.template_name, context)

    def post(self, request):
        update = request.POST.get('uuid') != ''
        data = json.loads(request.POST['deck'])

        if update:
            self._update_deck(request, data)
        else:
            self._save_deck(request, data)

        return redirect('/user')

    def _create_deck(self):
        return {
            'cards': [{}],  # empty card list with dummy card
            'template': self.dynamic_template
        }

    def _load_deck(self, request):
        user = User.objects.get(pk=request.session['user_id'])
        deck = get_object_or_404(Deck, user=user, uuid=request.GET['uuid'])     # check if user owns the deck
        cards = Card.objects.filter(deck=deck)

        return {
            'deck': utils.serialize(deck),
            'card_ids': list(map(lambda card: card.pk, cards)),
            'cards': utils.serialize(cards),
            'template': self.dynamic_template,
        }

    def _save_deck(self, request, data):
        from uuid import uuid4

        user = User.objects.get(pk=request.session['user_id'])
        data['uuid'] = uuid4()

        deck = Deck(
            user=user,
            name=data['name'],
            description=data['description'],
            uuid=data['uuid'],
            date_created=date.today(),
            last_modified=date.today()
        )

        deck.save()
        self._save_cards(request, deck, data)
        messages.success(request, f'Deck "{deck.name}" created successfully.')

    def _save_cards(self, request, deck, data):
        term_images = request.FILES.getlist('term-image')
        definition_images = request.FILES.getlist('definition-image')

        for card in data['cards']:
            term_image = term_images.pop(0) if card['term_image'] != '' else None
            definition_image = definition_images.pop(0) if card['definition_image'] != '' else None

            Card(
                deck=deck,
                term=card['term'],
                term_image=self._make_unique(term_image),
                definition=card['definition'],
                definition_image=self._make_unique(definition_image)
            ).save()

    def _update_deck(self, request, data):
        deck = Deck.objects.get(uuid=data['uuid'])
        self._update(deck, data, 'name', 'description')
        deck.last_modified = date.today()
        deck.save()
        self._update_cards(request, deck, data)

    def _update_cards(self, request, deck, data):
        cards = Card.objects.filter(deck=deck)

        for card in cards:
            # get corresponding card by primary key from POST
            new = list(filter(lambda post: card.pk == post['pk'], data['cards']))
            try:
                new = new.pop()
                self._update(card, new, 'term', 'definition')
                self._update_images(request, card, new)
            except IndexError:
                # card is not present in POST because it was deleted
                card.delete()

        # filter out and save newly added cards
        data['cards'] = list(filter(lambda card: card['pk'] is None, data['cards']))
        self._save_cards(request, deck, data)

    def _update_images(self, request, card, new):
        from os.path import basename

        modified = False
        term_images = request.FILES.getlist('term-image')
        definition_images = request.FILES.getlist('definition_image')

        if basename(card.term_image.name) != new['term_image']:
            term_image = term_images.pop(0) if new['term_image'] != '' else None
            card.term_image = self._make_unique(term_image)
            modified = True
        if basename(card.definition_image.name) != new['definition_image']:
            definition_image = definition_images.pop(0) if new['definition_image'] else None
            card.definition_image = self._make_unique(definition_image)
            modified = True

        if modified:
            card.save()

    def _update(self, model, data, *keys):
        """
        Parameters
        ----------
        model : Model
                The model to update
        data : dict
                Contains the new data for the model.
        *keys :
                Which fields are need to be updated.
        """
        modified = False

        for key in keys:
            if model.__dict__[key] != data[key]:
                model.__dict__[key] = data[key]
                modified = True

        if modified:
            model.save()

    def _make_unique(self, file, unique_id_length=7):
        from random import choice
        from string import ascii_letters, digits

        if file:
            name, ext = file.name.split('.')
            unique_id = ''.join(choice(ascii_letters + digits) for _ in range(unique_id_length))
            name = name + '_' + unique_id
            file.name = name + '.' + ext

        return file
