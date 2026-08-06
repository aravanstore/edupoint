from django.contrib import admin
from django.utils.html import format_html
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'rating_stars', 'is_approved', 'order', 'created_at')
    list_editable = ('is_approved', 'order')
    list_filter = ('is_approved', 'rating')
    search_fields = ('name', 'text')

    def rating_stars(self, obj):
        stars = '⭐' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color:#f59e0b;">{}</span>', stars)
    rating_stars.short_description = 'Оценка'
