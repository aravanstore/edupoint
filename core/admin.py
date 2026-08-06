from django.contrib import admin
from django.utils.html import format_html
from .models import SiteSettings, GalleryImage, ContactMessage


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Контакты', {'fields': ('phone', 'whatsapp', 'email', 'address')}),
        ('Социальные сети', {'fields': ('instagram', 'telegram', 'youtube', 'tiktok')}),
        ('Брендинг', {'fields': ('logo', 'favicon')}),
        ('SEO', {'fields': ('meta_title', 'meta_description')}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'preview', 'order', 'uploaded_at')
    list_filter = ('category',)
    list_editable = ('order',)
    search_fields = ('title',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" height="60" style="object-fit:cover;border-radius:4px;">', obj.image.url)
        return '—'
    preview.short_description = 'Превью'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'is_read', 'created_at')
    list_filter = ('is_read',)
    list_editable = ('is_read',)
    readonly_fields = ('name', 'email', 'phone', 'message', 'created_at')
    search_fields = ('name', 'phone', 'email')
