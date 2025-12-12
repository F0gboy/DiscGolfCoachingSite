from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile, Conversation, Message, Response, RoundResult


def create_user(username: str, role: str = Profile.ATHLETE) -> User:
	nuser = User.objects.create_user(username=username, password='pass1234')
	nuser.profile.role = role
	nuser.profile.save()
	return nuser


class ProfileModelTests(TestCase):
	def test_profile_created_with_default_role(self):
		user = User.objects.create_user(username='athlete', password='pass1234')
		self.assertTrue(hasattr(user, 'profile'))
		self.assertEqual(user.profile.role, Profile.ATHLETE)

	def test_coach_role_persists(self):
		coach = create_user('coach', role=Profile.COACH)
		self.assertEqual(coach.profile.role, Profile.COACH)


class ConversationAndMessageTests(TestCase):
	def setUp(self):
		self.athlete = create_user('athlete')
		self.coach = create_user('coach', role=Profile.COACH)
		self.conversation = Conversation.objects.create(
			athlete=self.athlete,
			coach=self.coach,
			subject='Backhand form',
		)

	def test_message_and_response_relationship(self):
		message = Message.objects.create(
			conversation=self.conversation,
			sender=self.athlete,
			text='Please review my throw.',
		)
		response = Response.objects.create(message=message, text='Looks good!')
		self.assertEqual(message.conversation, self.conversation)
		self.assertEqual(response.message, message)
		self.assertEqual(str(self.conversation), f"Conversation: {self.athlete.username} -> {self.coach.username} ({self.conversation.created_at:%Y-%m-%d})")


class RoundResultTests(TestCase):
	def test_score_display_and_ordering(self):
		athlete = create_user('rounder')
		first = RoundResult.objects.create(
			athlete=athlete,
			course_name='Local Park',
			score_relative=2,
		)
		second = RoundResult.objects.create(
			athlete=athlete,
			course_name='Local Park',
			score_relative=-3,
		)
		self.assertEqual(first.score_display, '+2')
		self.assertEqual(second.score_display, '-3')
		results = list(RoundResult.objects.all())
		self.assertEqual(results[0], second)


class HomeViewTests(TestCase):
	def setUp(self):
		self.athlete = create_user('home-athlete')
		self.coach = create_user('home-coach', role=Profile.COACH)

	def test_dashboard_for_authenticated_athlete_lists_coaches(self):
		self.client.force_login(self.athlete)
		response = self.client.get(reverse('coachingsite:home'))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'site/dashboard.html')
		self.assertIn('coaches', response.context)
		self.assertIn(self.coach, response.context['coaches'])

	def test_dashboard_for_coach_lists_athletes(self):
		self.client.force_login(self.coach)
		response = self.client.get(reverse('coachingsite:home'))
		self.assertEqual(response.status_code, 200)
		self.assertIn('athletes', response.context)
		self.assertIn(self.athlete, response.context['athletes'])


class SubmitMessageViewTests(TestCase):
	def setUp(self):
		self.athlete = create_user('submit-athlete')
		self.coach = create_user('submit-coach', role=Profile.COACH)

	def test_athlete_can_submit_message_and_conversation_created(self):
		self.client.force_login(self.athlete)
		data = {
			'sender_name': 'Athlete',
			'sender_email': 'a@example.com',
			'text': 'Need help with drives',
			'coach': self.coach.id,
		}
		response = self.client.post(reverse('coachingsite:submit'), data)
		self.assertEqual(response.status_code, 302)
		self.assertEqual(Message.objects.count(), 1)
		message = Message.objects.first()
		self.assertEqual(message.sender, self.athlete)
		self.assertIsNotNone(message.conversation)
		self.assertEqual(message.conversation.coach, self.coach)


class ConversationDetailViewTests(TestCase):
	def setUp(self):
		self.athlete = create_user('thread-athlete')
		self.coach = create_user('thread-coach', role=Profile.COACH)
		self.other_user = create_user('intruder')
		self.conversation = Conversation.objects.create(
			athlete=self.athlete,
			coach=self.coach,
			subject='Putting',
		)

	def test_third_party_cannot_access_conversation(self):
		self.client.force_login(self.other_user)
		url = reverse('coachingsite:conversation_detail', args=[self.conversation.pk])
		response = self.client.get(url)
		self.assertEqual(response.status_code, 403)

	def test_participants_can_post_message(self):
		self.client.force_login(self.athlete)
		url = reverse('coachingsite:conversation_detail', args=[self.conversation.pk])
		response = self.client.post(url, {'text': '  New update  '})
		self.assertEqual(response.status_code, 302)
		self.assertEqual(self.conversation.messages.count(), 1)
		message = self.conversation.messages.first()
		self.assertEqual(message.text, 'New update')
		self.assertEqual(message.sender, self.athlete)
