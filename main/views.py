import json

from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect
from datetime import date
from uuid import uuid4
from . import authentication as auth, utils
from .models import *


# Create your views here.


def index(request):
    utils.delete_past_session(request)

    if request.GET.get('view') is None:
        return redirect('/?view=login')

    login = 'login'
    register = 'register'

    form = request.GET['view']

    # prevent nonsensical urls
    if form != login and form != register:
        raise Http404()

    if request.method == 'POST':
        # handle login
        if form == login:
            if auth.validate_login(request):
                # create session for user
                login_user = User.objects.get(username=request.POST['username'])
                request.session['user_id'] = login_user.pk
                return redirect('/user')
        # handle registration
        elif form == register:
            if auth.validate_registration(request):
                messages.success(request, 'Registration successful!')
                return redirect('/?view=login')

    context = {
        'form': form,
        'index': True   # this changes the header depending on if the user is authenticated
    }

    return render(request, 'main/index.html', context)


def user(request):
    if not utils.user_exists(request):
        return redirect('/?view=login')

    user_id = request.session.get('user_id')
    User.objects.filter(pk=user_id).update(last_login=date.today())
    current_user = User.objects.get(pk=user_id)

    context = {
        'username': current_user.username,
        'date_created': current_user.date_created,
        'decks': utils.serialize_model(Deck, user=current_user),
        'template': utils.load_view_template('deck_view_template.html'),
    }

    if request.method == 'POST':
        # user deletes a deck
        if request.POST.get('delete'):
            deck_id = request.POST['delete']
            Deck.objects.filter(pk=deck_id).delete()
            messages.success(request, 'Deck deleted successfully.')
            return redirect('/user')
        # user changes his/her password
        elif auth.change_password(request):
            messages.success(request, 'Password changed successfully.')
            return redirect('/user')

    return render(request, 'main/user.html', context)


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
            'original': utils.get_deck_json(deck)
        }

        return render(request, 'main/editor.html', context)

    # save deck
    if request.method == 'POST':
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
            term_image = term_images.pop(0) if card['term_image'] else None
            definition_image = definition_images.pop(0) if card['definition_image'] else None

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


def form(request):
    if request.method == 'POST':
        print(request.POST)

    return render(request, 'main/form.html')