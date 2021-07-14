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

    if request.method == 'POST':
        deck = Deck(
            user=parent_user,
            name=request.POST['name'],
            description=request.POST['description'],
            uuid=uuid4(),
            date_created=date.today(),
            last_modified=date.today()
        )
        deck.save()

        for card in utils.get_card_list(request):
            Card(
                deck=deck,
                term=card['term'],
                term_image=card.get('term_image'),
                definition=card['definition'],
                definition_image=card.get('definition_image')
            ).save()

        messages.success(request, 'Deck {} created successfully.'.format(request.POST['name']))
        return redirect('/user')

    context = {
        'decks': utils.serialize_model(Deck, user=parent_user),
        'cards': list(range(1)),
        'template': utils.load_view_template('card_view_template.html'),
    }

    return render(request, 'main/editor.html', context)
