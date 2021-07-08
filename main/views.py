from django.contrib import messages
from django.http import Http404
from django.shortcuts import render, redirect
from datetime import date
from uuid import uuid4
from . import authentication as auth, models, utils


# Create your views here.


def index(request):
    if request.GET.get('view') is None:
        return redirect('/?view=login')

    utils.delete_past_session(request)

    login = 'login'
    register = 'register'
    form = request.GET['view']

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
    if not utils.user_exists(request):
        return redirect('/?view=login')

    user_id = request.session.get('user_id')
    models.User.objects.filter(pk=user_id).update(last_login=date.today())
    current_user = models.User.objects.get(pk=user_id)
    template = utils.load_view_template('deck_view_template.html')

    context = {
        'username': current_user.username,
        'date_created': current_user.date_created,
        'decks': utils.serialize_model(models.Deck, user=current_user),
        'template': template,
    }

    if request.method == 'POST':
        # user deletes a deck
        if request.POST.get('delete'):
            deck_id = request.POST['delete']
            models.Deck.objects.filter(pk=deck_id).delete()
            messages.success(request, 'Deck successfully deleted.')
            return redirect('/user')
        # user changes his/her password
        elif auth.change_password(request):
            messages.success(request, 'Password successfully changed.')
            return redirect('/user')

    return render(request, 'main/user.html', context)


def editor(request):
    if not utils.user_exists(request):
        return redirect('/?view=login')

    if request.method == 'POST':
        # Deck created
        parent_user = models.User.objects.get(pk=request.session['user_id'])
        models.Deck(
            user=parent_user,
            name=request.POST['name'],
            description=request.POST['description'],
            uuid=uuid4(),
            date_created=date.today(),
            last_modified=date.today()
        ).save()

        context = {
            'decks': utils.serialize_model(models.Deck, user=parent_user)
        }

        return redirect('/user', context)

    return render(request, 'main/editor.html')
