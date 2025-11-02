from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Message
from .forms import MessageForm, ResponseForm
from django.contrib.auth import login
from .forms import RegistrationForm


def home(request):
	"""Render the site home page."""
	return render(request, "site/home.html")


def submit_message(request):
	"""Allow users to submit a message or video."""
	if request.method == 'POST':
		form = MessageForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			return redirect(reverse('coachingsite:submit') + '?sent=1')
	else:
		form = MessageForm()
	return render(request, 'site/submit.html', {'form': form})


def inbox(request):
	"""List messages for the coach to review."""
	messages = Message.objects.order_by('-created_at')
	return render(request, 'site/inbox.html', {'messages': messages})


def message_detail(request, pk):
	msg = get_object_or_404(Message, pk=pk)
	if request.method == 'POST':
		form = ResponseForm(request.POST, request.FILES)
		if form.is_valid():
			resp = form.save(commit=False)
			resp.message = msg
			resp.save()
			msg.responded = True
			msg.save()
			return redirect('coachingsite:message_detail', pk=pk)
	else:
		form = ResponseForm()
	return render(request, 'site/message_detail.html', {'message': msg, 'form': form})


def register(request):
	"""Simple registration view that creates a user and logs them in."""
	if request.method == 'POST':
		form = RegistrationForm(request.POST)
		if form.is_valid():
			role = form.cleaned_data.pop('role')
			user = form.save()
			# set staff/superuser based on role
			if role == 'admin':
				user.is_staff = True
				user.is_superuser = True
			elif role == 'coach':
				user.is_staff = True
			user.save()
			# assign role on profile
			user.profile.role = role
			user.profile.save()
			login(request, user)
			return redirect('/')
	else:
		form = RegistrationForm()
	return render(request, 'registration/register.html', {'form': form})
