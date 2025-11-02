from django.contrib import admin
from .models import Article, Message, Response
from .models import Profile


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
	list_display = ('title', 'published_date')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'sender_name', 'sender_email', 'created_at', 'responded')
	readonly_fields = ('created_at',)


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
	list_display = ('id', 'message', 'created_at')
	readonly_fields = ('created_at',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'role')
