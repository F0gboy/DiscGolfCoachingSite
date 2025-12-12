import json

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q, Avg, Min, Max, Count
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .forms import MessageForm, ResponseForm, ProfileForm, RegistrationForm, RoundResultForm
from .models import Message, Conversation, Profile, RoundResult


def home(request):
	"""Render the site home page."""
	# If user is authenticated, show the coaching platform dashboard.
	if request.user.is_authenticated:
		# dashboard will include a coach list for starting conversations
		# If user is a coach, show all athletes to message
		if request.user.profile.role == Profile.COACH:
			athletes = User.objects.filter(profile__role=Profile.ATHLETE)
			return render(request, "site/dashboard.html", {'athletes': athletes})
		coaches = User.objects.filter(profile__role=Profile.COACH)
		return render(request, "site/dashboard.html", {'coaches': coaches})
	# otherwise show the marketing home page
	return render(request, "site/home.html")


def submit_message(request):
	"""Allow users to submit a message or video."""
	if request.method == 'POST':
		form = MessageForm(request.POST, request.FILES, user=request.user)
		if form.is_valid():
			msg = form.save(commit=False)
			# associate sender if logged in
			if request.user.is_authenticated:
				msg.sender = request.user
			# if coach selected, find or create a conversation
			coach = form.cleaned_data.get('coach')
			if coach:
				# find existing conversation between this athlete and coach
				athlete = msg.sender or None
				convo = None
				if athlete:
					convo = Conversation.objects.filter(athlete=athlete, coach=coach).first()
				if not convo:
					convo = Conversation.objects.create(athlete=athlete or None, coach=coach, subject='')
				msg.conversation = convo
			msg.save()
			return redirect(reverse('coachingsite:submit') + '?sent=1')
	else:
		form = MessageForm(user=request.user)
	return render(request, 'site/submit.html', {'form': form})


def inbox(request):
	"""List messages for the coach to review."""
	# show conversations rather than raw messages
	if request.user.is_authenticated and request.user.profile.role == Profile.COACH:
		convos = Conversation.objects.filter(coach=request.user).order_by('-updated_at')
	elif request.user.is_authenticated:
		convos = Conversation.objects.filter(athlete=request.user).order_by('-updated_at')
	else:
		convos = Conversation.objects.none()
	return render(request, 'site/inbox.html', {'conversations': convos})


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


@login_required
def conversation_detail(request, pk):
	convo = get_object_or_404(Conversation, pk=pk)
	# access control: only participant users or superusers can access
	user = request.user
	if not (user == convo.athlete or user == convo.coach or user.is_superuser):
		return HttpResponseForbidden('You do not have permission to view this conversation')
	# show messages in thread; only include messages that have non-whitespace text or a video
	# use a regex lookup to ensure we skip whitespace-only text messages
	# optimize with select_related/prefetch_related to avoid N+1 lookups in templates
	thread_msgs = (
		convo.messages
		.select_related('sender', 'conversation')
		.prefetch_related('responses')
		.filter(Q(text__regex=r'\S') | Q(video__isnull=False))
		.order_by('created_at')
	)
	# single composer form: use MessageForm to create new messages within conversation
	composer = MessageForm(user=request.user)
	if request.method == 'POST':
		composer = MessageForm(request.POST, request.FILES, user=request.user)
		if composer.is_valid():
			msg = composer.save(commit=False)
			# normalize/trim text to avoid saving whitespace-only messages
			if msg.text:
				msg.text = msg.text.strip()
			# if there's no text and no video, ignore the post (don't create empty messages)
			if not msg.text and not msg.video:
				return redirect('coachingsite:conversation_detail', pk=pk)
			# Prevent messaging yourself
			if convo.coach == convo.athlete:
				return HttpResponseForbidden('You cannot message yourself')
			msg.sender = request.user
			msg.conversation = convo
			msg.save()
			convo.updated_at = msg.created_at
			convo.save()
			return redirect('coachingsite:conversation_detail', pk=pk)

	return render(request, 'site/conversation_detail.html', {'conversation': convo, 'thread_messages': thread_msgs, 'composer': composer})


@login_required
def start_conversation(request, coach_id):
	# only athletes can start conversations (or any authenticated user if you prefer)
	# The URL param may be a coach id when an athlete initiates,
	# or an athlete id when a coach initiates. Handle both cases.
	initiator = request.user
	# If initiator is a coach, they want to message the athlete whose id is passed.
	if initiator.profile.role == Profile.COACH:
		coach = initiator
		athlete = get_object_or_404(User, pk=coach_id)
	else:
		athlete = initiator
		coach = get_object_or_404(User, pk=coach_id)

	# disallow starting a conversation with yourself
	if coach == athlete:
		return HttpResponseForbidden('You cannot start a conversation with yourself')

	convo = Conversation.objects.filter(athlete=athlete, coach=coach).first()
	if not convo:
		convo = Conversation.objects.create(athlete=athlete, coach=coach, subject='')
	return redirect('coachingsite:conversation_detail', pk=convo.pk)


def register(request):
	"""Simple registration view that creates a user and logs them in."""
	if request.method == 'POST':
		form = RegistrationForm(request.POST)
		if form.is_valid():
			role = form.cleaned_data.pop('role')
			user = form.save()
			# Do not allow public registration to create admin/superuser accounts.
			# Coaches are made staff so they can access coach areas if needed.
			if role == 'coach':
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


@login_required
def profile(request):
	return render(request, 'site/profile.html', {'user': request.user})



@login_required
def edit_profile(request):
	profile = request.user.profile
	if request.method == 'POST':
		form = ProfileForm(request.POST, request.FILES, instance=profile)
		if form.is_valid():
			form.save()
			return redirect('coachingsite:profile')
	else:
		form = ProfileForm(instance=profile)
	return render(request, 'site/profile_settings.html', {'form': form})


@login_required
def progress(request):
	"""Allow athletes to log rounds and coaches to review progress over time, per course."""

	profile = getattr(request.user, 'profile', None)
	role = getattr(profile, 'role', None)
	is_coach = role == Profile.COACH
	is_athlete = role == Profile.ATHLETE

	athletes = None
	selected_athlete = None
	form = None

	if is_coach:
		athletes = User.objects.filter(profile__role=Profile.ATHLETE).order_by('username')
		athlete_id = request.GET.get('athlete')
		if athlete_id:
			selected_athlete = get_object_or_404(User, pk=athlete_id, profile__role=Profile.ATHLETE)
		else:
			selected_athlete = athletes.first() if athletes.exists() else None
	elif is_athlete:
		selected_athlete = request.user
		if request.method == 'POST':
			form = RoundResultForm(request.POST)
			if 'course_name' in form.fields:
				form.fields['course_name'].widget.attrs['list'] = 'courseSuggestions'
			if form.is_valid():
				round_result = form.save(commit=False)
				round_result.athlete = request.user
				round_result.save()
				messages.success(request, 'Round logged.')
				return redirect('coachingsite:progress')
		else:
			form = RoundResultForm()
			if 'course_name' in form.fields:
				form.fields['course_name'].widget.attrs['list'] = 'courseSuggestions'
	else:
		return HttpResponseForbidden('Progress tracking is limited to coaches and athletes.')

	rounds_qs = RoundResult.objects.filter(athlete=selected_athlete) if selected_athlete else RoundResult.objects.none()

	def course_label(name):
		return name.strip() if name else 'Unspecified course'

	course_groups = rounds_qs.values('course_name').annotate(
		total_rounds=Count('id'),
		avg_score=Avg('score_relative'),
		best=Min('score_relative'),
		worst=Max('score_relative'),
	).order_by('course_name')

	course_options = []
	course_stats = []
	for group in course_groups:
		name = group['course_name'] or ''
		value = name if name else '__none'
		label = course_label(name)
		course_options.append({'value': value, 'label': label, 'count': group['total_rounds']})
		course_stats.append({
			'label': label,
			'rounds': group['total_rounds'],
			'avg': group['avg_score'],
			'best': group['best'],
			'worst': group['worst'],
		})

	course_filter = request.GET.get('course', '')
	filtered_qs = rounds_qs
	if course_filter:
		if course_filter == '__none':
			filtered_qs = filtered_qs.filter(Q(course_name__isnull=True) | Q(course_name__exact=''))
		else:
			filtered_qs = filtered_qs.filter(course_name=course_filter)

	selected_course_label = 'All courses'
	if course_filter == '__none':
		selected_course_label = course_label('')
	elif course_filter:
		selected_course_label = course_label(course_filter)

	entries = filtered_qs.order_by('-played_on', '-created_at')
	chart_qs = filtered_qs.order_by('played_on', 'created_at')

	course_suggestions = []
	if selected_athlete:
		course_suggestions = list(
			rounds_qs
			.exclude(course_name__isnull=True)
			.exclude(course_name__exact='')
			.values_list('course_name', flat=True)
			.distinct()
		)
		course_suggestions.sort(key=lambda name: name.lower())

	aggregates = filtered_qs.aggregate(
		avg_score=Avg('score_relative'),
		best=Min('score_relative'),
		worst=Max('score_relative'),
	) if selected_athlete else {'avg_score': None, 'best': None, 'worst': None}

	chart_points = [
		{
			'date': entry.played_on.strftime('%Y-%m-%d'),
			'label': entry.course_name or 'Round',
			'score': entry.score_relative,
		}
		for entry in chart_qs
	]

	context = {
		'form': form,
		'entries': entries,
		'chart_data': json.dumps(chart_points, cls=DjangoJSONEncoder),
		'aggregate': aggregates,
		'round_count': filtered_qs.count(),
		'overall_round_count': rounds_qs.count(),
		'selected_course': course_filter,
		'selected_course_label': selected_course_label,
		'course_options': course_options,
		'course_stats': course_stats,
		'course_suggestions': course_suggestions,
		'selected_athlete': selected_athlete,
		'athletes': athletes,
		'is_coach': is_coach,
		'is_athlete': is_athlete,
	}
	return render(request, 'site/progress.html', context)
