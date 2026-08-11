from django.contrib import admin
from .models import (
    StudentApplication, GroupSet, ApplicationStatusHistory,
    WaitlistEntry, Branch, SpendEntry,
)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    list_filter = ('is_active',)


@admin.register(GroupSet)
class GroupSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'teacher', 'schedule_display', 'start_date',
                    'capacity', 'reserved_count', 'status', 'created_at')
    list_filter = ('status', 'course', 'branch')
    search_fields = ('name', 'course__name')
    readonly_fields = ('reserved_count', 'fill_percent', 'created_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Основное', {'fields': ('name', 'course', 'teacher', 'branch', 'status')}),
        ('Расписание', {'fields': ('days', 'start_time', 'end_time', 'start_date')}),
        ('Места', {'fields': ('capacity', 'reserved_count', 'fill_percent')}),
        ('Группа', {'fields': ('group',)}),
        ('Служебное', {'fields': ('created_by', 'created_at')}),
    )


@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'age', 'course', 'group_set', 'source',
                    'status', 'created_at')
    list_filter = ('status', 'source', 'course__category', 'group_set')
    list_editable = ('status',)
    search_fields = ('name', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'status_changed_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Заявитель', {'fields': ('name', 'phone', 'age')}),
        ('Курс / набор', {'fields': ('course', 'group_set', 'language_level')}),
        ('Маркетинг', {'fields': ('source', 'comment', 'notes')}),
        ('Статус', {'fields': ('status', 'status_changed_at', 'created_at', 'updated_at')}),
    )


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('application', 'old_status', 'new_status', 'changed_by', 'created_at')
    list_filter = ('new_status',)
    search_fields = ('application__name', 'application__phone')
    readonly_fields = ('created_at',)


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'group_set', 'notified', 'created_at')
    list_filter = ('notified', 'group_set')
    search_fields = ('name', 'phone')


@admin.register(SpendEntry)
class SpendEntryAdmin(admin.ModelAdmin):
    list_display = ('source', 'month', 'amount', 'note')
    list_filter = ('source', 'month')
    search_fields = ('note',)
