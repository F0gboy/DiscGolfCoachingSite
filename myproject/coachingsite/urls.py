from django.urls import path
from . import views

app_name = 'coachingsite'

urlpatterns = [
    path('', views.home, name='home'),
    path('submit/', views.submit_message, name='submit'),
    path('inbox/', views.inbox, name='inbox'),
    path('message/<int:pk>/', views.message_detail, name='message_detail'),
]
