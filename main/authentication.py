import re

from django.contrib import messages
from django.contrib.auth import password_validation as pv
from django.contrib.auth.validators import UnicodeUsernameValidator
from datetime import date
from hashlib import sha256
from .models import User


def hash_password(password):
    return sha256(password.encode()).hexdigest()


def validate_login(request):
    login_username = request.POST['username']
    login_password = hash_password(request.POST['password'])

    if not User.objects.filter(username=login_username, password=login_password).exists():
        messages.error(request, 'Wrong username or password.')
        return False
    return True


def validate_registration(request):
    new_username = request.POST['username']
    new_email = request.POST['email']
    password1 = request.POST['password1']
    password2 = request.POST['password2']

    valid_username = _validate_username(new_username, request)
    valid_email = _validate_email(new_email, request)
    valid_password = _validate_password(password1, password2, request)

    if valid_username and valid_email and valid_password:
        # create new user
        User(
            username=new_username,
            email=new_email,
            password=hash_password(password1),
            date_created=date.today(),
            last_login=date.today()
        ).save()
        return True
    return False


def change_password(request):
    user_id = request.session['user_id']
    old_password = request.POST['old_password']
    password1 = request.POST['password1']
    password2 = request.POST['password2']

    if not User.objects.filter(pk=user_id, password=hash_password(old_password)).exists():
        messages.error(request, 'Wrong password.')
        return False

    if old_password == password1 or old_password == password2:
        messages.error(request, 'New password cannot be the old one.')
        return False

    if _validate_password(password1, password2, request):
        User.objects.filter(pk=user_id).update(password=hash_password(password1))
        return True


def _validate_username(username, request):
    validator = UnicodeUsernameValidator()

    # check for not allowed characters
    if not re.match(validator.regex, username):
        messages.error(request, validator.message)
        return False

    if len(username) < 4:
        messages.error(request, 'Username must be at least 4 characters.')
        return False

    if User.objects.filter(username=username).exists():
        messages.error(request, 'Username already in use.')
        return False

    return True


def _validate_email(email, request):
    if User.objects.filter(email=email).exists():
        messages.error(request, 'E-mail already registered.')
        return False
    return True


def _validate_password(password1, password2, request):
    if password1 != password2:
        messages.error(request, 'Incorrect password validation.')
        return False

    try:
        pv.validate_password(password1)
        return True
    except pv.ValidationError as e:
        messages.error(request, e.messages[0])
        return False
