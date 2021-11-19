from django.urls import path
from .views import *

urlpatterns = [
    path('', IndexView.as_view()),
    path('login/', IndexView.as_view(site='login')),
    path('register/', IndexView.as_view(site='register')),
    path('recovery/', IndexView.as_view(site='recovery')),

    path('search/<page>', SearchView.as_view(), name='page'),

    path('user/', UserView.as_view()),
    path('user/<page>', UserView.as_view(), name='page'),
    path('user/search/<page>', UserView.as_view(site='search'), name='page'),
    path('user/manage/', UserView.as_view(site='manage')),
    path('checkout/', CheckoutView.as_view()),
    path('checkout/<page>', CheckoutView.as_view(), name='page'),

    path('editor/', EditorView.as_view()),

    path('flashcards/', FlashcardsView.as_view()),
    path('learn/', LearnView.as_view()),

    path('key/', CryptoView.as_view()),
]
