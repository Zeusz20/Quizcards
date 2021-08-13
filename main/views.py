import json

from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from datetime import date
from os.path import basename
from . import authentication as auth, paging, testgen, utils
from .models import *


class IndexView(View):
    template_name = 'main/index/index.html'

    def get(self, request):
        if request.GET.get('logout') is not None:
            utils.delete_past_session(request)

        if utils.user_exists(request):
            return redirect('/user')

        if request.GET.get('view') is None:
            return redirect('/?view=login')

        context = {
            'form': request.GET['view'],
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


class SearchView(View):
    template_name = 'main/search.html'
    page_manager = paging.get_default_page_manager(paging.SEARCH_VIEW_PAGE_SIZE)

    def get(self, request):
        if len(self.page_manager.object_list) == 0:
            self._get_object_list(request)

        context = {
            'page': self.page_manager.page(request.GET['page']),
        }

        return render(request, self.template_name, context)

    def _get_object_list(self, request):
        if utils.user_exists(request):
            user = User.objects.get(pk=request.session['user_id'])
            self.page_manager.object_list = paging.get_decks(user, request.GET['query'], local=False)
        else:
            self.page_manager.object_list = paging.get_decks(None, request.GET['query'], local=False)


class UserView(View):
    template_name = 'main/user/user.html'
    display_page_manager = None     # used for displaying all of user's decks with pagination
    search_page_manager = None      # used for displaying a select number of user's decks (local search)

    def get(self, request):
        if not utils.user_exists(request):
            return redirect('/')

        user = User.objects.get(pk=request.session['user_id'])
        context = self._get_user_data(user)

        if len(request.GET) == 0:
            # user freshly logged in
            user.last_login = date.today()
            user.save()
            return redirect('/user/?page=1')

        if request.GET.get('page'):
            query = request.GET.get('query')

            if query is not None:
                # user searched for decks
                if self.search_page_manager is None or self.search_page_manager.query != query:
                    decks = paging.get_decks(user, query, local=True)
                    self.search_page_manager = paging.QueryPaginator(query, decks, paging.USER_VIEW_PAGE_SIZE)

                page = self._get_page(self.search_page_manager, request.GET['page'])
            else:
                # no query, display user's decks with pagination
                if self.search_page_manager is not None:
                    # reset search page manager
                    self.search_page_manager.query = ''

                if self.display_page_manager is None:
                    decks = paging.get_decks(user)
                    self.display_page_manager = paging.Paginator(decks, paging.USER_VIEW_PAGE_SIZE)

                page = self._get_page(self.display_page_manager, request.GET['page'])

            context.update(page)
            return render(request, self.template_name, context)

        # render user's manage page
        return render(request, self.template_name, context)

    def post(self, request):
        if request.POST.get('delete'):
            self._handle_delete(request)    # user deletes a deck
            return redirect('/user')
        else:
            self._handle_password_change(request)
            return redirect('/user')

    def _get_user_data(self, user):
        return {
            'username': user.username,
            'date_created': user.date_created,
        }

    def _get_page(self, page_manager, page):
        return {
            'page': page_manager.page(page),
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
    template_name = 'main/editor/editor.html'

    def get(self, request):
        if not utils.user_exists(request):
            return redirect('/')

        if request.GET.get('uuid'):
            context = self._load_deck(request)
        else:
            context = {
                'cards': [{}],  # empty card list with an empty card
            }

        return render(request, self.template_name, context)

    def post(self, request):
        data = json.loads(request.POST['deck'])
        update = data.get('uuid')

        self._make_unique(request.FILES)

        if update:
            self._update_deck(request, data)
        else:
            self._save_deck(request, data)

        return redirect('/user')

    def _load_deck(self, request):
        user = User.objects.get(pk=request.session['user_id'])
        deck = get_object_or_404(Deck, user=user, uuid=request.GET['uuid'])     # check if user owns the deck
        cards = Card.objects.filter(deck=deck)

        return {
            'deck': utils.serialize(deck),
            'cards': utils.serialize(cards),
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
            term_image = term_images.pop(0) if card['term_image'] else None
            definition_image = definition_images.pop(0) if card['definition_image'] else None

            Card(
                deck=deck,
                term=card['term'],
                term_image=term_image,
                definition=card['definition'],
                definition_image=definition_image
            ).save()

    def _update_deck(self, request, data):
        Deck.objects.filter(uuid=data['uuid']).update()
        deck = Deck.objects.get(uuid=data['uuid'])
        data['last_modified'] = date.today()
        self._update(deck, data, 'name', 'description', 'last_modified')
        self._update_cards(request, deck, data)
        messages.success(request, f'Deck "{deck.name}" updated successfully.')

    def _update_cards(self, request, deck, data):
        cards = Card.objects.filter(deck=deck)

        for card in cards:
            # get corresponding card by primary key from POST
            new = list(filter(lambda post: card.pk == post['pk'], data['cards']))
            if len(new) != 0:
                new = new.pop()
                self._update(card, new, 'term', 'definition')
                self._update_images(request, card, new)
            else:
                # card is not present in POST because it was deleted
                card.delete()

        # filter out and save newly added cards
        data['cards'] = list(filter(lambda card: card['pk'] is None, data['cards']))
        self._save_cards(request, deck, data)

    def _update_images(self, request, card, new):
        modified = False
        term_images = request.FILES.getlist('term-image')
        definition_images = request.FILES.getlist('definition-image')

        if basename(card.term_image.name) != new['term_image']:
            term_image = term_images.pop(0) if new['term_image'] else None
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

    def _make_unique(self, files, unique_id_length=7):
        for image in ('term-image', 'definition-image'):
            for file in files.getlist(image):
                if file:
                    name, ext = file.name.split('.')
                    unique_id = utils.random_string(unique_id_length)
                    name = name + '_' + unique_id
                    file.name = name + '.' + ext


class FlashcardsView(View):
    template_name = 'main/study/flashcards/flashcards.html'

    def get(self, request):
        context = self._get_flashcards(request.GET['uuid'])
        return render(request, self.template_name, context)

    def post(self, request):
        context = self._get_flashcards(request.GET['uuid'])
        return render(request, self.template_name, context)

    def _get_flashcards(self, uuid):
        deck = get_object_or_404(Deck, uuid=uuid)
        cards = Card.objects.filter(deck=deck)
        return {
            'cards': utils.serialize(cards),
        }


class LearnView(View):
    template_name = 'main/study/learn/learn.html'
    page_manager = None

    def get(self, request):
        if self.page_manager is None:
            questions = testgen.generate_questions(request.GET['uuid'])
            self.page_manager = paging.Paginator(questions, 1)

        context = {
            'page': self.page_manager.page(request.GET['q']),
        }

        return render(request, self.template_name, context)

    def post(self, request):
        questions = testgen.generate_questions(request.GET['uuid'], request.POST['start'])
        self.page_manager = paging.Paginator(questions, 1)

        context = {
            'page': self.page_manager.page(request.GET['q']),
        }

        return render(request, self.template_name, context)


class StudyView(View):
    template_name = 'main/study/study.html'

    def get(self, request):
        deck = get_object_or_404(Deck, uuid=request.GET['uuid'])
        cards = Card.objects.filter(deck=deck)
        start_with = request.GET.get('start_with', 'term')

        if request.GET['type'] == 'study':
            context = {
                'question': testgen.get(request, start_with),
            }
        elif request.GET['type'] == 'write':
            context = {}
        elif request.GET['type'] == 'test':
            context = {}
        else:
            # default type: flashcards
            context = {
                'cards': utils.serialize(cards),
            }

        context.update({
            'start_with': start_with,
        })
        return render(request, self.template_name, context)
