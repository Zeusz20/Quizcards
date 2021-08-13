from django.core.paginator import Paginator
from django.db.models import Q
from .models import Deck

USER_VIEW_PAGE_SIZE = 7
SEARCH_VIEW_PAGE_SIZE = 10


def get_default_page_manager(per_page=1):
    return Paginator(list(), per_page)


def get_decks(user=None, query='', local=False):
    if user is None:
        # non logged in user's global sear
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


class QueryPaginator(Paginator):
    def __init__(self, query='', object_list=[], per_page=1):
        super().__init__(object_list, per_page)
        self.query = query
