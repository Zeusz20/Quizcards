from django.urls import path
from .views import *

urlpatterns = [
    path('', IndexView.as_view()),
    path('login/', IndexView.as_view(form='login')),
    path('register/', IndexView.as_view(form='register')),

    path('search/<page>', SearchView.as_view(), name='page'),

    path('user/', UserView.as_view()),
    path('user/<page>', UserView.as_view(), name='page'),
    path('user/search/<page>', UserView.as_view(site='search'), name='page'),
    path('user/manage/', UserView.as_view(site='manage')),

    path('editor/', EditorView.as_view()),

    path('flashcards/', FlashcardsView.as_view()),
    path('learn/<page>', LearnView.as_view(), name='page'),
]
