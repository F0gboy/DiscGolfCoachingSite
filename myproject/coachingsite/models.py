from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver


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
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (ATHLETE, 'Athlete'),
        (COACH, 'Coach'),
        (ADMIN, 'Administrator'),
    ]

    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ATHLETE)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


# Create or update Profile automatically when a User is created
@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()