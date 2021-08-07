from django.urls import path
from .views import *

urlpatterns = [
    path('', IndexView.as_view()),
    path('user/', UserView.as_view()),
    path('editor/', EditorView.as_view()),
    path('search/', SearchView.as_view()),
]
