from django.contrib import admin
from .models import Exam


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'full_name', 'duration', 'price', 'is_active', 'order')
    list_editable = ('is_active', 'order', 'price')
    fieldsets = (
        ('Основное', {'fields': ('name', 'full_name', 'image', 'duration', 'price')}),
        ('Описание', {'fields': ('description', 'preparation_program', 'benefits')}),
        ('Публикация', {'fields': ('is_active', 'order')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )
