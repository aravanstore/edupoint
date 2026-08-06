from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import (
    UserProfile, Book, Group, StudentProfile, ParentProfile, TeacherProfile,
    Grade, Attendance, Homework, HomeworkSubmission, Payment,
    PaymentExtension, Announcement, Notification, ActivityLog,
)


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    fk_name = 'user'
    can_delete = False


class ParentProfileInline(admin.StackedInline):
    model = ParentProfile
    fk_name = 'user'
    can_delete = False


class TeacherProfileInline(admin.StackedInline):
    model = TeacherProfile
    fk_name = 'user'
    can_delete = False


class LmsUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'role_display')
    list_filter = ('is_staff', 'is_superuser', 'profile__role')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def role_display(self, obj):
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return '—'
    role_display.short_description = 'Роль'


admin.site.unregister(User)
admin.site.register(User, LmsUserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'order', 'duration_months', 'price_per_month', 'is_active')
    list_filter = ('category', 'is_active')
    list_editable = ('order', 'price_per_month', 'is_active')
    search_fields = ('name',)


class StudentInline(admin.TabularInline):
    model = StudentProfile
    extra = 0


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'teacher', 'book', 'days', 'start_time', 'end_time',
                    'student_count', 'capacity', 'status')
    list_filter = ('status', 'course__category')
    search_fields = ('name', 'course__name')
    inlines = [StudentInline]

    def student_count(self, obj):
        return obj.student_count()
    student_count.short_description = 'Учеников'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'book', 'book_progress', 'parent', 'is_active', 'frozen')
    list_filter = ('is_active', 'group', 'book')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')
    autocomplete_fields = ['user']

    def frozen(self, obj):
        return obj.is_frozen()
    frozen.short_description = 'Заморожен'
    frozen.boolean = True


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'teacher', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'value', 'date', 'teacher')
    list_filter = ('group', 'date')
    search_fields = ('student__user__username', 'student__user__first_name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'date', 'status')
    list_filter = ('group', 'status', 'date')
    search_fields = ('student__user__username', 'student__user__first_name')
    date_hierarchy = 'date'


class SubmissionInline(admin.TabularInline):
    model = HomeworkSubmission
    extra = 0


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'teacher', 'due_date', 'created_at')
    list_filter = ('group', 'due_date')
    search_fields = ('title', 'description')
    inlines = [SubmissionInline]


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    list_display = ('homework', 'student', 'submitted_at', 'is_late')
    list_filter = ('is_late', 'homework__group')
    search_fields = ('student__user__username', 'student__user__first_name')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'amount', 'method', 'is_confirmed', 'paid_at')
    list_filter = ('method', 'is_confirmed', 'month')
    search_fields = ('student__user__username', 'student__user__first_name')
    date_hierarchy = 'month'


@admin.register(PaymentExtension)
class PaymentExtensionAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'new_due_date', 'reason', 'created_at')
    search_fields = ('student__user__username', 'student__user__first_name')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'author', 'is_active', 'created_at')
    list_filter = ('group', 'is_active')
    search_fields = ('title', 'text')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'text', 'link', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'text')


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'target', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'action', 'target', 'details')
    date_hierarchy = 'created_at'
    readonly_fields = ('user', 'action', 'target', 'details', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
