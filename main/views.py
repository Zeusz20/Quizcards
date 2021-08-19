from django.contrib import messages
from django.core.paginator import Paginator
from django.db.transaction import atomic
from django.shortcuts import redirect, render as django_render
from django.views.generic import View
from abc import ABCMeta, abstractmethod
from database_locks import locked
from datetime import date
from os.path import basename
from . import authentication as auth, testgen, utils
from .models import *


class BaseView(View, metaclass=ABCMeta):
    template_name = ''
    session_keys = tuple()

    def render(self, request, **kwargs):
        context = self.get_context(request, **kwargs)
        return django_render(request, self.template_name, context)

    @abstractmethod
    def get_context(self, request, **kwargs):
        pass

    def create_context(self, **kwargs):
        return kwargs


class PagingView(BaseView, metaclass=ABCMeta):
    page_manager = None

    @abstractmethod
    def init_page_manager(self, request):
        pass


class IndexView(BaseView):
    template_name = 'main/index/index.html'
    form = None

    def get(self, request):
        if request.GET.get('logout') is not None:
            request.session.flush()
        if utils.user_exists(request):
            return redirect('/user')
        if self.form is None:
            return redirect('/login')

        return super().render(request)

    def post(self, request):
        if self.form == 'login':
            self.handle_login(request)
            return redirect('/user')
        elif self.form == 'register':
            self.handle_registration(request)
            return redirect('/login')

    def get_context(self, request, **kwargs):
        return self.create_context(form=self.form)

    def handle_login(self, request):
        if auth.validate_login(request):
            user = User.objects.get(username=request.POST['username'])
            request.session['user_id'] = user.pk    # create session for user

    def handle_registration(self, request):
        if auth.validate_registration(request):
            messages.success(request, 'Registration successful!')


class SearchView(PagingView):
    template_name = 'main/search.html'
    session_keys = ('global_search', 'user_id')

    def get(self, request, **kwargs):
        utils.session_clean_up(self, request)
        return super().render(request, **kwargs)

    def post(self, request, **kwargs):
        request.session['global_search'] = request.POST['query'].strip()
        return super().render(request, **kwargs)

    def get_context(self, request, **kwargs):
        self.init_page_manager(request)
        return self.create_context(page=self.page_manager.page(kwargs['page']))

    def init_page_manager(self, request):
        try:
            user = User.objects.get(pk=request.session.get('user_id'))
        except User.DoesNotExist:
            user = None

        decks = utils.get_decks_from_query(user, request.session['global_search'], local=False)
        self.page_manager = Paginator(decks, utils.SEARCH_VIEW_PAGE_SIZE)


class UserView(PagingView):
    template_name = 'main/user/user.html'
    session_keys = ('local_search', 'user_id')
    site = None

    def get(self, request, **kwargs):
        if not utils.user_exists(request):
            return redirect('/')

        utils.session_clean_up(self, request)
        user = User.objects.get(pk=request.session['user_id'])

        # fresh login tasks
        if self.site is None and kwargs.get('page') is None:
            user.last_login = date.today()
            user.save()
            return redirect('/user/1')

        kwargs['user'] = user   # save user for context
        return super().render(request, **kwargs)

    def post(self, request, **kwargs):
        if request.POST.get('search'):
            request.session['local_search'] = request.POST['query'].strip()
            return redirect('/user/search/1')
        elif request.POST.get('delete'):
            self.handle_deck_delete(request)
            return redirect('/user')
        else:
            self.handle_password_change(request)
            return redirect('/user')

    def get_context(self, request, **kwargs):
        context = self.create_context(user=kwargs['user'], site=self.site)

        if self.site != 'search':
            # delete possible previous local search session
            if request.session.get('local_search'):
                del request.session['local_search']

        if kwargs.get('page'):
            self.init_page_manager(request)
            context.update(page=self.page_manager.page(kwargs['page']))

        return context

    def init_page_manager(self, request):
        user = request.session['user_id']
        query = request.session.get('local_search') or ''
        decks = utils.get_decks_from_query(user, query, local=True)
        self.page_manager = Paginator(decks, utils.USER_VIEW_PAGE_SIZE)

    @atomic
    @locked
    def handle_deck_delete(self, request):
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
    session_keys = ('checkout', 'user_id')

    def get(self, request, **kwargs):
        if request.GET.get('checkout'):
            request.session['checkout'] = request.GET['checkout']
            return redirect('/checkout/1')

        utils.session_clean_up(self, request)
        return super().render(request, **kwargs)

    def get_context(self, request, **kwargs):
        self.init_page_manager(request)
        return self.create_context(page=self.page_manager.page(kwargs['page']))

    def init_page_manager(self, request):
        checkout_user = User.objects.get(username=request.session['checkout'])
        decks = Deck.objects.filter(user=checkout_user)
        self.page_manager = Paginator(decks, utils.USER_VIEW_PAGE_SIZE)


class EditorView(BaseView):
    template_name = 'main/editor/editor.html'
    session_keys = ('user_id', 'uuid')

    def get(self, request):
        if not utils.user_exists(request):
            return redirect('/')

        if request.GET.get('uuid'):
            request.session['uuid'] = request.GET['uuid']
            return redirect('/editor')

        utils.session_clean_up(self, request)
        return super().render(request)

    def post(self, request):
        from json import loads
        data = loads(request.POST['deck'])
        update = data.get('uuid')   # if exists a uuid in POST we update

        self._make_unique(request.FILES)

        if update:
            self.update_deck(request, data)
        else:
            self.save_deck(request, data)

        return redirect('/user')

    def get_context(self, request, **kwargs):
        if request.session.get('uuid'):
            # load deck
            user = User.objects.get(pk=request.session['user_id'])
            deck = Deck.objects.get(user=user, uuid=request.session['uuid'])  # check if user owns the deck
            cards = Card.objects.filter(deck=deck)
            return self.create_context(deck=deck, cards=cards)
        else:
            return self.create_context(cards=[{}])   # empty card list with an empty card

    @atomic
    @locked
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

    @atomic
    @locked
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


class StudyView(BaseView):
    """Base class for those view classes which handle the studying aspect of quizcards."""
    session_keys = ('user_id', 'uuid')

    def get_context(self, request, **kwargs):
        return self.create_context(start_with=self.start_with(request))

    def save_settings(self, request):
        request.session['start_with'] = request.POST['start-with']

    def start_with(self, request):
        return request.session.get('start_with') or 'term'


class FlashcardsView(StudyView):
    template_name = 'main/study/flashcards/flashcards.html'

    def get(self, request):
        if request.GET.get('uuid'):
            request.session['uuid'] = request.GET['uuid']
            return redirect('/flashcards')

        utils.session_clean_up(self, request)
        return super().render(request)

    def post(self, request):
        super().save_settings(request)
        return super().render(request)

    def get_context(self, request, **kwargs):
        deck = Deck.objects.get(uuid=request.session['uuid'])
        cards = Card.objects.filter(deck=deck)
        context = super().get_context(request)
        context.update(cards=cards)
        return context


class LearnView(StudyView):
    template_name = 'main/study/learn/learn.html'

    def get(self, request):
        if request.GET.get('uuid'):
            request.session['uuid'] = request.GET['uuid']
            return redirect('/learn')

        utils.session_clean_up(self, request)
        return super().render(request)

    def post(self, request):
        super().save_settings(request)
        return super().render(request)

    def get_context(self, request, **kwargs):
        uuid = request.session['uuid']
        start_with = self.start_with(request)
        context = super().get_context(request, **kwargs)
        context.update(questions=testgen.generate_questions(uuid, start_with))
        return context
