from django.contrib import admin
from .models import Article, Message, Response, RoundResult, Profile


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


@admin.register(RoundResult)
class RoundResultAdmin(admin.ModelAdmin):
	list_display = ('athlete', 'course_name', 'score_relative', 'played_on', 'created_at')
	list_filter = ('played_on', 'athlete')
	search_fields = ('course_name', 'athlete__username', 'athlete__first_name', 'athlete__last_name')
	readonly_fields = ('created_at',)
