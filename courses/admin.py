from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Course, CourseSchedule


class CourseScheduleInline(admin.TabularInline):
    model = CourseSchedule
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('flag_emoji', 'name', 'language_code', 'order')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'teacher', 'level', 'price', 'is_featured', 'is_active')
    list_filter = ('category', 'level', 'is_featured', 'is_active')
    list_editable = ('is_featured', 'is_active', 'price')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'description')
    inlines = [CourseScheduleInline]
    fieldsets = (
        ('Основное', {'fields': ('category', 'teacher', 'name', 'slug', 'image')}),
        ('Описание', {'fields': ('short_description', 'description')}),
        ('Параметры', {'fields': ('level', 'duration', 'lessons_per_week', 'price')}),
        ('Публикация', {'fields': ('is_featured', 'is_active')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )
