from django.contrib import admin
from .models import Video, Lesson, UserFavorite


class LessonInline(admin.StackedInline):
    model = Lesson
    extra = 0


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['id', 'episode', 'title', 'tag', 'date', 'youtuber']
    list_filter = ['tag']
    search_fields = ['title', 'episode']
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['id', 'video', 'created_at']


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ['user', 'video', 'created_at']
