from django.core.paginator import Paginator
from django.db.models import Q
from .models import Deck

USER_VIEW_PAGE_SIZE = 7
SEARCH_VIEW_PAGE_SIZE = 10

DECK_PAGE_MANAGERS = dict()
SEARCH_PAGE_MANAGERS = dict()


def get_deck_page_manager(user):
    manager = DECK_PAGE_MANAGERS.get(user.pk)

    if manager is None:
        manager = Paginator(Deck.objects.filter(user=user), USER_VIEW_PAGE_SIZE)
        DECK_PAGE_MANAGERS[user.pk] = manager

    return manager


def get_search_page_manager(user, get):
    local = bool(get.get('local'))
    query = get['query']

    manager_key = user.pk if user else 'guest'
    manager = SEARCH_PAGE_MANAGERS.get(manager_key)

    if manager is None:
        manager = SearchPageManager(user, query, local)
        SEARCH_PAGE_MANAGERS['guest'] = manager
        print('creating manager')

    return manager


class SearchPageManager(Paginator):
    def __init__(self, user, query, local):
        if local:
            decks = Deck.objects.filter(
                Q(user=user),
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        else:
            if user is None:
                decks = Deck.objects.filter(
                    Q(name__icontains=query) | Q(description__icontains=query)
                )
            else:
                decks = Deck.objects.filter(
                    ~Q(user=user),
                    Q(name__icontains=query) | Q(description__icontains=query)
                )

        page_size = USER_VIEW_PAGE_SIZE if local else SEARCH_VIEW_PAGE_SIZE
        super().__init__(decks, page_size)
