USER_VIEW_PAGE_SIZE = 7
SEARCH_VIEW_PAGE_SIZE = 10


def user_exists(request):
    return request.session.get('user_id') is not None


def session_clean_up(view, request):
    for key in dict(request.session).keys():
        if key not in view.session_keys:
            del request.session[key]


def show_form_error_messages(request, form):
    from django.contrib import messages

    for error_type in form.errors:
        for error_text in form.errors[error_type]:
            messages.error(request, error_text)


def get_image_url(image_path):
    if image_path == '':
        return image_path

    from django.conf import settings
    from os.path import basename, join

    root = basename(settings.MEDIA_ROOT)
    return join(root, basename(image_path))


def random_string(length):
    from random import choice
    from string import ascii_letters, digits
    return ''.join(choice(ascii_letters + digits) for _ in range(length))


def validate_datetime(day, hour, minute):
    if not 1 <= day <= 7:
        raise ValueError(day)
    if not 0 <= hour <= 23:
        raise ValueError(hour)
    if not 0 <= minute <= 59:
        raise ValueError(minute)


def get_decks_from_query(user=None, query='', local=False):
    from django.db.models import Q
    from .models import Deck

    if user is None:
        # non logged in user's global search
        return Deck.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if query == '':
        # logged in user's deck pagination
        return Deck.objects.filter(user=user)

    if local:
        # logged in user's local search
        return Deck.objects.filter(
            Q(user=user),
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        # logged in user's global search
        return Deck.objects.filter(
            ~Q(user=user),
            Q(name__icontains=query) | Q(description__icontains=query)
        )
