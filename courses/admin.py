from django.contrib import admin
from .models import Course, Quest, QuestProgress


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'tier', 'icon', 'order', 'is_free', 'is_published')
    list_filter = ('tier', 'is_free', 'is_published')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Quest)
class QuestAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'course', 'difficulty', 'xp_reward', 'command_trigger', 'is_published')
    list_filter = ('course', 'difficulty', 'is_published')
    search_fields = ('title', 'description', 'command_trigger')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(QuestProgress)
class QuestProgressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'quest', 'is_completed', 'attempts', 'completed_at')
    list_filter = ('is_completed', 'completed_at')
    search_fields = ('user__username', 'quest__title')