from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.transaction import atomic
from django.shortcuts import redirect, render as django_render
from django.utils.translation import gettext as _
from django.views.generic import View
from abc import ABCMeta, abstractmethod
from datetime import date
from . import forms, testgen, utils
from .models import *


class BaseView(View, metaclass=ABCMeta):
    template_name = ''
    session_keys = tuple()

    def render(self, request, **kwargs):
        utils.session_clean_up(self, request)
        context = self.get_context(request, **kwargs)
        return django_render(request, self.template_name, context)

    @abstractmethod
    def get_context(self, request, **kwargs):
        pass

    def _create_context(self, **kwargs):
        return kwargs


class PagingView(BaseView, metaclass=ABCMeta):
    page_manager = None

    @abstractmethod
    def init_page_manager(self, request):
        pass


class IndexView(BaseView):
    template_name = 'main/index/index.html'
    site = None

    def get(self, request):
        if request.GET.get('logout') is not None:
            logout(request)

        if request.user.is_authenticated:
            return redirect('/user')
        if self.site is None:
            return redirect('/login')

        return super().render(request)

    def post(self, request):
        if self.site == 'login':
            return self.handle_login(request)
        elif self.site == 'register':
            return self.handle_registration(request)
        elif self.site == 'recovery':
            return self.recover_password(request)

    def get_context(self, request, **kwargs):
        return self._create_context(site=self.site)

    @utils.sensitive
    def handle_login(self, request):
        user = authenticate(request, username=request.POST['username'], password=request.POST['password'])
        request.user = user

        if user is not None:
            login(request, user)
            return redirect('/user')
        else:
            messages.error(request, _('Wrong username or password.'))
            return redirect('/login')

    @utils.sensitive
    def handle_registration(self, request):
        form = forms.AccountCreationForm(request.POST)
        success_msg = _('Registration successful!')

        if forms.validate_form(request, form, success_msg):
            return redirect('/login')
        else:
            return redirect('/register')

    def recover_password(self, request):
        username = request.POST['username']
        email = request.POST['email']

        try:
            # refresh user's password
            user = User.objects.select_for_update().get(username=username, email=email)
            new_password = utils.random_string(32)
            user.set_password(new_password)
            user.save()

            # inform user about the changes
            send_mail(
                'Password Recovery',
                _('Dear %s!\nWe\'ve refreshed your password.\nYou can login with: %s\n\nSincerely\nQuizcards Support')
                % (user.username, new_password),   # format string
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user.email],
            )
            msg = _('We\'ve sent an email containing your new password.')
            messages.success(request, msg)
            return redirect('/login')
        except User.DoesNotExist:
            msg = _('No match for "%s" and "%s".') % (username, email)
            messages.error(request, msg)
            return redirect('/recovery')


class SearchView(PagingView):
    template_name = 'main/search.html'
    session_keys = ('global_search', )

    def get(self, request, **kwargs):
        return super().render(request, **kwargs)

    def post(self, request, **kwargs):
        request.session['global_search'] = request.POST['query'].strip()
        return super().render(request, **kwargs)

    def get_context(self, request, **kwargs):
        self.init_page_manager(request)
        return self._create_context(page=self.page_manager.page(kwargs['page']))

    def init_page_manager(self, request):
        decks = utils.get_decks_from_query(request.user, request.session['global_search'], local=False)
        self.page_manager = Paginator(decks, utils.SEARCH_VIEW_PAGE_SIZE)


class UserView(PagingView):
    template_name = 'main/user/user.html'
    session_keys = ('local_search', )
    site = None

    @utils.auth_required
    def get(self, request, **kwargs):
        # fresh login tasks
        if self.site is None and kwargs.get('page') is None:
            request.user.save()  # update last login date
            return redirect('/user/1')

        return super().render(request, **kwargs)

    def post(self, request, **kwargs):
        if request.POST.get('search'):
            request.session['local_search'] = request.POST['query'].strip()
            return redirect('/user/search/1')

        if request.POST.get('delete'):
            self.handle_deck_delete(request)
            return redirect('/user')

        if request.POST.get('change'):
            self.manage_user(request)  # handle email or password change
            return redirect('/user/manage/')

    def get_context(self, request, **kwargs):
        context = self._create_context(user=request.user, site=self.site)

        if self.site != 'search':
            # delete possible previous local search session
            if request.session.get('local_search'):
                del request.session['local_search']

        if self.site == 'manage':
            password_form = forms.PasswordChangeForm(request.user)
            email_form = forms.EmailChangeForm(request.user)
            context.update(password_form=password_form, email_form=email_form)
        else:
            if kwargs.get('page'):
                self.init_page_manager(request)
                context.update(page=self.page_manager.page(kwargs['page']))

        return context

    def init_page_manager(self, request):
        query = request.session.get('local_search')
        decks = utils.get_decks_from_query(request.user, query, local=True)
        self.page_manager = Paginator(decks, utils.USER_VIEW_PAGE_SIZE)

    @atomic
    def handle_deck_delete(self, request):
        deck_id = request.POST['delete']
        deck = Deck.objects.select_for_update().get(pk=deck_id)
        name = deck.name
        deck.delete()
        messages.success(request, _(f'Deck "{name}" was successfully deleted.'))

    @utils.sensitive
    def manage_user(self, request):
        """Handles email and password changes."""

        password_change = request.POST['change'] == 'password'

        if password_change:
            form = forms.PasswordChangeForm(request.user, request.POST)
            success_msg = _('Password changed successfully.')
        else:
            form = forms.EmailChangeForm(request.user, request.POST)
            success_msg = _('E-mail changed successfully.')

        forms.validate_form(request, form, success_msg, password_change)


class CheckoutView(PagingView):
    template_name = 'main/user/checkout.html'
    session_keys = ('checkout', )

    def get(self, request, **kwargs):
        if request.GET.get('checkout'):
            request.session['checkout'] = request.GET['checkout']
            return redirect('/checkout/1')

        return super().render(request, **kwargs)

    def get_context(self, request, **kwargs):
        self.init_page_manager(request)
        return self._create_context(page=self.page_manager.page(kwargs['page']))

    def init_page_manager(self, request):
        checkout_user = User.objects.get(username=request.session['checkout'])
        decks = Deck.objects.filter(user=checkout_user)
        self.page_manager = Paginator(decks, utils.USER_VIEW_PAGE_SIZE)


class EditorView(BaseView):
    template_name = 'main/editor/editor.html'
    session_keys = ('uuid', )

    @utils.auth_required
    def get(self, request):
        if request.GET.get('uuid'):
            request.session['uuid'] = request.GET['uuid']
            return redirect('/editor')

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
            deck = Deck.objects.get(user=request.user, uuid=request.session['uuid'])  # check if user owns the deck
            return self._create_context(deck=deck, cards=Card.objects.filter(deck=deck))
        else:
            return self._create_context(cards=[{}])  # empty card list with an empty card

    @atomic
    def save_deck(self, request, data):
        from uuid import uuid4

        data['uuid'] = uuid4()
        deck = Deck(
            user=request.user,
            name=data['name'],
            description=data['description'],
            uuid=data['uuid'],
            date_created=date.today(),
            last_modified=date.today()
        )
        deck.save()
        self.save_cards(request, deck, data)
        messages.success(request, _(f'Deck "{deck.name}" created successfully.'))

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
    def update_deck(self, request, data):
        deck = Deck.objects.select_for_update().get(uuid=data['uuid'])
        data['last_modified'] = date.today()
        self._update(deck, data, 'name', 'description', 'last_modified')
        self.update_cards(request, deck, data)
        messages.success(request, _(f'Deck "{deck.name}" updated successfully.'))

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
    """Base class for those view classes which handle the studying aspect of Quizcards."""

    session_keys = ('settings', 'uuid', )

    def get(self, request):
        if request.GET.get('uuid'):
            request.session['uuid'] = request.GET['uuid']
            return redirect(self.redirect_to())

        if request.session.get('settings') is None:
            request.session['settings'] = testgen.get_settings()

        return super().render(request)

    def post(self, request):
        request.session['settings'] = testgen.get_settings(request.POST)
        return redirect(self.redirect_to())  # POST/REDIRECT/GET in order to prevent resubmitting settings

    def get_context(self, request, **kwargs):
        settings = request.session['settings']
        deck = Deck.objects.get(uuid=request.session['uuid'])
        return self._create_context(settings=settings, deck=deck)

    def redirect_to(self):
        return '/' + self.__class__.__name__[:-4].lower()


class FlashcardsView(StudyView):
    template_name = 'main/study/flashcards/flashcards.html'

    def get_context(self, request, **kwargs):
        deck = Deck.objects.get(uuid=request.session['uuid'])
        context = super().get_context(request)
        context.update(cards=Card.objects.filter(deck=deck))
        return context


class LearnView(StudyView):
    template_name = 'main/study/learn/learn.html'

    def get_context(self, request, **kwargs):
        uuid = request.session['uuid']
        answer_with = request.session['settings']['answer_with']
        context = super().get_context(request, **kwargs)
        context.update(questions=testgen.generate_questions(uuid, answer_with))
        return context


class CryptoView(View):
    """Grants access to RSA public key. Available through PUT request."""

    def get(self, request):
        from django.http import Http404
        raise Http404

    def put(self, request):
        from django.http import HttpResponse
        from .crypto import crypto
        return HttpResponse(crypto.public_key())
