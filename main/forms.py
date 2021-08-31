from django.forms import EmailField, ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import User

# user as default forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordChangeForm


class AccountCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')


class EmailChangeForm(ModelForm):
    new_email = EmailField(required=True)

    class Meta:
        model = User
        fields = ('email', )

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user: User = user
        self.fields['new_email'].widget.attrs.update({'autofocus': 'autofocus'})

    def clean_email(self):
        return self.cleaned_data.get('new_email')

    def save(self, commit=True):
        self.user.email = self.cleaned_data['new_email']
        if commit:
            self.user.save()
        return self.user


def validate_form(request, form, success_msg, update_session=False):
    from django.contrib import messages
    from django.contrib.auth import update_session_auth_hash

    if form.is_valid():
        form.save()
        if update_session:
            update_session_auth_hash(request, request.user)
        messages.success(request, success_msg)
        return True
    else:
        # show form error messages
        for field in form.errors:
            for error in form.errors[field]:
                messages.error(request, error)
        return False
