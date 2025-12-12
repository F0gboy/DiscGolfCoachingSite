from django.urls import path
from . import views

app_name = 'coachingsite'

urlpatterns = [
    path('', views.home, name='home'),
    path('submit/', views.submit_message, name='submit'),
    path('inbox/', views.inbox, name='inbox'),
    path('message/<int:pk>/', views.message_detail, name='message_detail'),
    path('conversation/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('conversation/start/<int:coach_id>/', views.start_conversation, name='start_conversation'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('progress/', views.progress, name='progress'),
]
