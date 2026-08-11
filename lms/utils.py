from django.urls import reverse

from .models import ActivityLog, Notification


def notify_user(user, text, link=''):
    """Создаёт внутрисайтовое уведомление пользователю."""
    if not user or not user.is_authenticated:
        return
    Notification.objects.create(user=user, text=text, link=link)


def notify_student(student, text, link=''):
    if student and student.user:
        notify_user(student.user, text, link)


def log_activity(user, action, target='', details=''):
    """Записывает действие в журнал ActivityLog."""
    if not user or not user.is_authenticated:
        return
    ActivityLog.objects.create(
        user=user,
        action=str(action)[:100],
        target=str(target)[:300],
        details=str(details)[:500],
    )


def log_request_activity(request, action, target='', details=''):
    log_activity(request.user, action, target, details)


def homework_link(hw):
    return reverse('lms:student_homework')
