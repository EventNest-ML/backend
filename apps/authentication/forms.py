from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = User
        fields = ['email', 'firstname', 'lastname']
        error_class = 'error'


class CustomUserChangeForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['email', 'firstname', 'lastname']
        error_class = 'error'