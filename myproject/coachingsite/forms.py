from django import forms
from .models import Message, Response, RoundResult
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import AuthenticationForm


class MessageForm(forms.ModelForm):
    coach = forms.ModelChoiceField(queryset=User.objects.filter(profile__role='coach'), required=False, help_text='Choose a coach to send this to')

    class Meta:
        model = Message
        fields = ['sender_name', 'sender_email', 'text', 'video', 'coach']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # make the text field a small textarea and add bootstrap class
        if 'text' in self.fields:
            self.fields['text'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Write a message...'})
        # If a user is provided and is a coach, hide the coach selector
        if user and hasattr(user, 'profile') and user.profile.role == Profile.COACH:
            # coach field not applicable when coach is composing inside conversation
            if 'coach' in self.fields:
                del self.fields['coach']
        else:
            # otherwise, limit coach choices to active coaches only
            self.fields['coach'].queryset = User.objects.filter(profile__role=Profile.COACH)


class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['text', 'video']


class RegistrationForm(UserCreationForm):
    # Exclude the 'admin' role from public registration choices
    role = forms.ChoiceField(choices=[(Profile.ATHLETE, 'Athlete'), (Profile.COACH, 'Coach')], initial=Profile.ATHLETE)

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            # Apply Bootstrap classes
            if getattr(widget, 'input_type', '') == 'password':
                css = 'form-control'
            elif isinstance(field, forms.ChoiceField):
                css = 'form-select'
            else:
                css = 'form-control'
            existing = widget.attrs.get('class', '')
            widget.attrs['class'] = (existing + ' ' + css).strip()
            # set placeholder where appropriate
            if not widget.attrs.get('placeholder') and name not in ('password1', 'password2'):
                widget.attrs['placeholder'] = field.label


class CustomAuthenticationForm(AuthenticationForm):
    """AuthenticationForm that adds Bootstrap classes and placeholders to inputs."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'username' in self.fields:
            self.fields['username'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'you@example.com or username',
                'autofocus': 'autofocus'
            })
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.update({
                'class': 'form-control',
                'placeholder': 'Your password'
            })


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('full_name', 'bio', 'profile_picture')


class RoundResultForm(forms.ModelForm):
    class Meta:
        model = RoundResult
        fields = ['course_name', 'score_relative', 'played_on', 'notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        widgets = self.fields
        widgets['course_name'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Course name (optional)',
        })
        widgets['score_relative'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Relative score (e.g. -2, +5)',
        })
        widgets['played_on'].widget.attrs.update({
            'class': 'form-control',
        })
        widgets['notes'].widget.attrs.update({
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Notes (optional)',
        })
