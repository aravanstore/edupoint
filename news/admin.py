from django.contrib import admin
from .models import NewsPost, BlogPost


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'published_at', 'views')
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    list_filter = ('is_published',)
    date_hierarchy = 'published_at'
    readonly_fields = ('views',)
    fieldsets = (
        ('Основное', {'fields': ('title', 'slug', 'excerpt', 'content', 'image')}),
        ('Публикация', {'fields': ('is_published', 'views')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'published_at', 'views')
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content', 'tags')
    list_filter = ('is_published', 'category')
    date_hierarchy = 'published_at'
    readonly_fields = ('views',)
    fieldsets = (
        ('Основное', {'fields': ('title', 'slug', 'category', 'tags', 'excerpt', 'content', 'image')}),
        ('Публикация', {'fields': ('is_published', 'views')}),
        ('SEO', {'fields': ('meta_title', 'meta_description'), 'classes': ('collapse',)}),
    )
