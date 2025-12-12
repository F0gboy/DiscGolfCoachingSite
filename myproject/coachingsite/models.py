from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils import timezone


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    published_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Message(models.Model):
    """A message or video submitted by a user seeking coaching feedback."""
    sender_name = models.CharField(max_length=100, blank=True)
    sender_email = models.EmailField(blank=True)
    text = models.TextField(blank=True)
    video = models.FileField(upload_to='uploads/%Y/%m/%d', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)
    # link to a conversation if this message is part of one
    conversation = models.ForeignKey('Conversation', related_name='messages', on_delete=models.SET_NULL, null=True, blank=True)
    # optional sender user
    sender = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages')

    def __str__(self):
        name = self.sender_name or 'Anonymous'
        return f"{name} — {self.created_at:%Y-%m-%d %H:%M}"


class Response(models.Model):
    """A response from the coach to a Message; may include text and/or a video."""
    message = models.ForeignKey(Message, related_name='responses', on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    video = models.FileField(upload_to='responses/%Y/%m/%d', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to {self.message.id} at {self.created_at:%Y-%m-%d %H:%M}"


class Profile(models.Model):
    """User profile that stores a role for access control."""
    ATHLETE = 'athlete'
    COACH = 'coach'

    ROLE_CHOICES = [
        (ATHLETE, 'Athlete'),
        (COACH, 'Coach'),
    ]

    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ATHLETE)
    full_name = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profiles/%Y/%m/%d', blank=True, null=True)
    # For coaches: which athletes are assigned to them
    assigned_athletes = models.ManyToManyField('auth.User', related_name='assigned_coaches', blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


# Create or update Profile automatically when a User is created
@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()


class RoundResult(models.Model):
    """Stores a disc golf round result for progress tracking."""

    athlete = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='round_results',
    )
    course_name = models.CharField(max_length=255, blank=True)
    score_relative = models.IntegerField(help_text='Score relative to par (e.g. -2, +5)')
    played_on = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_on', '-created_at']

    def __str__(self):
        label = self.course_name or 'Round'
        return f"{self.athlete.username} — {label} ({self.score_display})"

    @property
    def score_display(self):
        return f"{self.score_relative:+d}"


class Conversation(models.Model):
    """A conversation thread between an athlete and a coach."""
    athlete = models.ForeignKey('auth.User', related_name='conversations_as_athlete', on_delete=models.CASCADE)
    coach = models.ForeignKey('auth.User', related_name='conversations_as_coach', on_delete=models.CASCADE)
    subject = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Conversation: {self.athlete.username} -> {self.coach.username} ({self.created_at:%Y-%m-%d})"