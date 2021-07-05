import uuid

from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect
from datetime import date
from . import authentication as auth, models, utils


# Create your views here.


def root(request):
    return redirect('/index/login')


def index(request, form):
    login = 'login'
    register = 'register'

    utils.delete_past_session(request)

    # prevent nonsensical urls
    if form != login and form != register:
        raise Http404()

    if request.method == 'POST':
        if form == login:
            # handle login
            if auth.validate_login(request):
                # create session for user
                login_user = models.User.objects.get(username=request.POST['username'])
                request.session['user_id'] = login_user.pk
                return redirect('/user')
        elif form == register:
            # handle registration
            if auth.validate_registration(request):
                messages.success(request, 'Successful registration!')
                return redirect('/index/login')

    return render(request, 'main/index.html', {'form': form})


def user(request):
    utils.redirect_if_no_user(request)

    user_id = request.session.get('user_id')
    if user_id is None:
        raise Http404()

    models.User.objects.filter(pk=user_id).update(last_login=date.today())
    current_user = models.User.objects.get(pk=user_id)

    ctx = {
        'username': current_user.username,
        'date_created': current_user.date_created,
        'decks': models.Deck.objects.filter(user=current_user),
    }

    # change password in user_manage
    if request.method == 'POST':
        if auth.change_password(request):
            messages.success(request, 'Password successfully changed.')

    return render(request, 'main/user.html', ctx)
