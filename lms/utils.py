from django.urls import reverse
from django.utils import timezone

from .models import ActivityLog, Notification, Payment, PaymentExtension


def bulk_frozen_student_ids(students):
    """Множество id учеников с просроченной оплатой — 2 запроса вместо
    is_frozen()/payment_status() в цикле по каждому ученику (N+1 запросов,
    заметно при сотнях учеников)."""
    ids = list(students.values_list('id', flat=True)) if hasattr(students, 'values_list') else [s.id for s in students]
    if not ids:
        return set()

    today = timezone.localdate()
    month_start = today.replace(day=1)

    paid_student_ids = set(
        Payment.objects.filter(
            student_id__in=ids, month__year=month_start.year,
            month__month=month_start.month, is_confirmed=True,
        ).values_list('student_id', flat=True)
    )
    extended_due = dict(
        PaymentExtension.objects.filter(
            student_id__in=ids, month__year=month_start.year, month__month=month_start.month,
        ).order_by('student_id', 'new_due_date').values_list('student_id', 'new_due_date')
    )
    return {
        sid for sid in ids
        if sid not in paid_student_ids and today > extended_due.get(sid, month_start)
    }


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
