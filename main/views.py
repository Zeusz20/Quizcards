import json

from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.generic import View
from datetime import date
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
    dynamic_template = utils.load_view_template('main/deck_view_template.html')

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
    dynamic_template = utils.load_view_template('main/card_view_template.html')

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
        update = request.POST.get('update')
        data = json.loads(request.POST['deck'])

        if update is not None:
            self._update_deck(request, data)
            return redirect('/user')
        else:
            self._save_deck(request, data)
            return redirect('/user')

    def _create_deck(self):
        return {
            'num_of_cards': list(range(1)),
            'template': self.dynamic_template
        }

    def _load_deck(self, request):
        uuid = request.GET['uuid']
        deck = Deck.objects.get(uuid=request.GET['uuid'])
        cards = list(Card.objects.filter(deck=deck))

        return {
            'deck': utils.serialize_model(Deck, uuid=uuid)[0],
            'cards': utils.serialize_model(Card, deck=deck),
            'num_of_cards': range(len(cards)),
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
                term_image=term_image,
                definition=card['definition'],
                definition_image=definition_image
            ).save()

    def _update_deck(self, request, data):
        deck = Deck.objects.get(uuid=data['uuid'])
        deck.last_modified = date.today()
        self._update(deck, data, 'name', 'description')
        self._update_cards(request, deck, data)

    def _update_cards(self, request, deck, data):
        cards = list(Card.objects.filter(deck=deck))

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

        self._clean_up_orphaned_files()

    def _update_images(self, request, card, new):
        from os.path import basename

        modified = False
        term_images = request.FILES.getlist('term-image')
        definition_images = request.FILES.getlist('definition_image')

        if basename(card.term_image.name) != new['term_image']:
            term_image = term_images.pop(0) if new['term_image'] != '' else None
            card.term_image = term_image
            modified = True
        if basename(card.definition_image.name) != new['definition_image']:
            definition_image = definition_images.pop(0) if new['definition_image'] else None
            card.definition_image = definition_image
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

    def _clean_up_orphaned_files(self):
        # TODO
        from django.conf import settings
        from os import listdir

        cards = list(Card.objects.all())
        images = list(map(lambda card: (card.term_image, card.definition_image), cards))
        term_images, definition_images = zip(*images)
        for file in listdir(settings.MEDIA_ROOT):
            pass
