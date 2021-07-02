from django.shortcuts import redirect


def redirect_if_no_user(request):
    if request.session.get('user_id') is None:
        redirect('/index/login')


def delete_past_session(request):
    if request.session.get('user_id') is not None:
        del request.session['user_id']
