from django import forms
from .models import Message, Response
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['sender_name', 'sender_email', 'text', 'video']


class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['text', 'video']


class RegistrationForm(UserCreationForm):
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, initial=Profile.ATHLETE)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
