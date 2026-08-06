from django.contrib import admin
from .models import StudentApplication


@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'age', 'course', 'language_level', 'status', 'created_at')
    list_filter = ('status', 'language_level', 'course__category')
    list_editable = ('status',)
    search_fields = ('name', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Заявитель', {'fields': ('name', 'phone', 'age')}),
        ('Курс', {'fields': ('course', 'language_level', 'comment')}),
        ('Статус', {'fields': ('status', 'created_at', 'updated_at')}),
    )
