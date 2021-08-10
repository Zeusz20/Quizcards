from django.core.paginator import Paginator
from django.db.models import Q
from .models import Deck

USER_VIEW_PAGE_SIZE = 7
SEARCH_VIEW_PAGE_SIZE = 10


def get_page(get, user=None):
    # param user is None for non logged in users
    if get.get('query'):
        # user searched for some decks
        local = get.get('local') is not None
        page_count = USER_VIEW_PAGE_SIZE if local else SEARCH_VIEW_PAGE_SIZE
        decks = get_decks(get['query'], user, local)
        page_manager = Paginator(decks, page_count)
        return page_manager.page(get['page'])
    else:
        # display user's decks with pagination
        page_manager = Paginator(Deck.objects.filter(user=user), USER_VIEW_PAGE_SIZE)
        return page_manager.page(get['page'])


def get_decks(query, user, local):
    if user is None:
        return Deck.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if local:
        return Deck.objects.filter(
            Q(user=user),
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    else:
        return Deck.objects.filter(
            ~Q(user=user),
            Q(name__icontains=query) | Q(description__icontains=query)
        )
