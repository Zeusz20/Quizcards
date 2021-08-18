import json

from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import View
from abc import ABCMeta, abstractmethod
from datetime import date
from os.path import basename
from . import authentication as auth, testgen, utils
from .models import *


class PagingView(View, metaclass=ABCMeta):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_manager = None

    @abstractmethod
    def init_page_manager(self, request):
        pass


class IndexView(View):
    template_name = 'main/index/index.html'
    form = None

    def get(self, request):
        if request.GET.get('logout') is not None:
            request.session.flush()

        if utils.user_exists(request):
            return redirect('/user')

        if self.form is None:
            return redirect('/login')

        if request.session.get('anonym') is None:
            # create session for anonymous user
            request.session['anonym'] = utils.random_string(32)

        context = {
            'form': self.form,
        }

        return render(request, self.template_name, context)

    def post(self, request):
        if self.form == 'login':
            self.handle_login(request)
            return redirect('/user')
        elif self.form == 'register':
            self.handle_registration(request)
            return redirect('/login')

    def handle_login(self, request):
        if auth.validate_login(request):
            user = User.objects.get(username=request.POST['username'])
            request.session['user_id'] = user.pk    # create session for user
            return redirect('/user')

    def handle_registration(self, request):
        if auth.validate_registration(request):
            messages.success(request, 'Registration successful!')


class SearchView(PagingView):
    template_name = 'main/search.html'

    def get(self, request, **kwargs):
        utils.clear_session(self, request)

        if self.page_manager is None:
            self.init_page_manager(request)

        context = {
            'page': self.page_manager.page(kwargs['page']),
        }

        return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        request.session['global_search'] = request.POST['query']
        self.init_page_manager(request)

        context = {
            'page': self.page_manager.page(kwargs['page']),
        }
        return render(request, self.template_name, context)

    def init_page_manager(self, request):
        try:
            user = User.objects.get(pk=request.session.get('user_id'))
        except User.DoesNotExist:
            user = None

        decks = utils.get_decks_from_query(user, request.session['global_search'], local=False)
        self.page_manager = Paginator(decks, utils.SEARCH_VIEW_PAGE_SIZE)


class UserView(PagingView):
    template_name = 'main/user/user.html'
    site = None

    def get(self, request, **kwargs):
        utils.clear_session(self, request)

        if not utils.user_exists(request):
            return redirect('/')

        user = User.objects.get(pk=request.session['user_id'])
        context = {
            'user': user,
            'site': self.site,
        }

        # fresh login tasks
        if self.site is None and kwargs.get('page') is None:
            user.last_login = date.today()
            user.save()
            return redirect('/user/1')

        # renders
        if self.site is None:
            context = self.get_home_page(request, context, **kwargs)
            return render(request, self.template_name, context)
        else:
            if self.site == 'search':
                context = self.get_search_page(request, context, **kwargs)
                return render(request, self.template_name, context)
            elif self.site == 'manage':
                return render(request, self.template_name, context)

    def post(self, request, **kwargs):
        if request.POST.get('search'):
            request.session['local_search'] = request.POST['query'].strip()
            return redirect('/user/search/1')
        elif request.POST.get('delete'):
            self.handle_delete(request)     # user deletes a deck
            return redirect('/user')
        else:
            self.handle_password_change(request)
            return redirect('/user')

    def init_page_manager(self, request):
        user = request.session['user_id']
        query = request.session.get('local_search') or ''
        decks = utils.get_decks_from_query(user, query, local=True)
        self.page_manager = Paginator(decks, utils.USER_VIEW_PAGE_SIZE)

    def get_home_page(self, request, context, **kwargs):
        if request.session.get('local_search'):
            del request.session['local_search']

        if self.page_manager is None:
            self.init_page_manager(request)

        context.update({
            'page': self.page_manager.page(kwargs['page']),
        })
        return context

    def get_search_page(self, request, context, **kwargs):
        self.init_page_manager(request)
        context.update({
            'page': self.page_manager.page(kwargs['page']),
        })
        return context

    def handle_delete(self, request):
        deck_id = request.POST['delete']
        deck = Deck.objects.get(pk=deck_id)
        name = deck.name
        deck.delete()
        messages.success(request, f'Deck "{name}" was successfully deleted.')

    def handle_password_change(self, request):
        if auth.change_password(request):
            messages.success(request, 'Password changed successfully.')


class CheckoutView(PagingView):
    template_name = 'main/user/checkout.html'

    def get(self, request, **kwargs):
        if not utils.user_exists(request):
            return redirect('/')

        if request.GET.get('checkout'):
            request.session['checkout'] = request.GET['checkout']
            return redirect('/checkout/1')

        self.init_page_manager(request)
        context = {
            'page': self.page_manager.page(kwargs['page'])
        }
        return render(request, self.template_name, context)

    def init_page_manager(self, request):
        checkout_user = get_object_or_404(User, username=request.session['checkout'])
        decks = Deck.objects.filter(user=checkout_user)
        self.page_manager = Paginator(decks, utils.USER_VIEW_PAGE_SIZE)


class EditorView(View):
    template_name = 'main/editor/editor.html'

    def get(self, request):
        if not utils.user_exists(request):
            return redirect('/')

        utils.clear_session(self, request)

        if request.GET.get('uuid'):
            request.session['uuid'] = request.GET['uuid']
            return redirect('/editor')

        if request.session.get('uuid') is not None:
            context = self.load_deck(request)
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
            self.update_deck(request, data)
        else:
            self.save_deck(request, data)

        return redirect('/user')

    def load_deck(self, request):
        user = User.objects.get(pk=request.session['user_id'])
        deck = get_object_or_404(Deck, user=user, uuid=request.session['uuid'])     # check if user owns the deck
        cards = Card.objects.filter(deck=deck)

        return {
            'deck': utils.serialize(deck),
            'cards': utils.serialize(cards),
        }

    def save_deck(self, request, data):
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
        self.save_cards(request, deck, data)
        messages.success(request, f'Deck "{deck.name}" created successfully.')

    def save_cards(self, request, deck, data):
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

    def update_deck(self, request, data):
        deck = Deck.objects.get(uuid=data['uuid'])
        data['last_modified'] = date.today()
        self._update(deck, data, 'name', 'description', 'last_modified')
        self.update_cards(request, deck, data)
        messages.success(request, f'Deck "{deck.name}" updated successfully.')

    def update_cards(self, request, deck, data):
        cards = Card.objects.filter(deck=deck)

        for card in cards:
            # get corresponding card by primary key from POST
            new = list(filter(lambda post: card.pk == post['pk'], data['cards']))
            if len(new) != 0:
                new = new.pop()
                self._update(card, new, 'term', 'definition')
                self.update_images(request, card, new)
            else:
                # card is not present in POST because it was deleted
                card.delete()

        # filter out and save newly added cards
        data['cards'] = list(filter(lambda card: card['pk'] is None, data['cards']))
        self.save_cards(request, deck, data)

    def update_images(self, request, card, new):
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


class StudyView(View):
    """Base class for those view classes which handle the studying aspect of quizcards."""

    def get(self, request):
        utils.clear_session(self, request)

    def post(self, request):
        """Handles 'start with' setting."""
        request.session['start_with'] = request.POST['start-with']

    def save_uuid_and_redirect(self, request, redirect_to):
        if request.GET.get('uuid'):
            request.session['uuid'] = request.GET['uuid']
            return redirect(redirect_to)
        return None

    def start_with(self, request):
        return request.session.get('start_with') or 'term'

    def get_settings(self, request):
        return {
            'start_with': self.start_with(request)
        }


class FlashcardsView(StudyView):
    template_name = 'main/study/flashcards/flashcards.html'

    def get(self, request):
        super().get(request)

        if request.GET.get('uuid'):
            return super().save_uuid_and_redirect(request, '/flashcards')

        context = self.get_flashcards(request)
        return render(request, self.template_name, context)

    def post(self, request):
        super().post(request)
        context = self.get_flashcards(request)
        return render(request, self.template_name, context)

    def get_flashcards(self, request):
        deck = get_object_or_404(Deck, uuid=request.session['uuid'])
        cards = Card.objects.filter(deck=deck)
        return {
            'cards': utils.serialize(cards),
            'start_with': self.start_with(request),
        }


class LearnView(StudyView):
    template_name = 'main/study/learn/learn.html'

    def get(self, request):
        super().get(request)

        if request.GET.get('uuid'):
            return super().save_uuid_and_redirect(request, '/learn')

        context = super().get_settings(request)
        context.update(self.get_questions(request))
        return render(request, self.template_name, context)

    def post(self, request):
        super().post(request)
        context = super().get_settings(request)
        context.update(self.get_questions(request))
        return render(request, self.template_name, context)

    def get_questions(self, request):
        return {
            'questions': testgen.generate_questions(request.session['uuid'], self.start_with(request)),
        }
