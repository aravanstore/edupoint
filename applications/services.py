"""Сервисные функции CRM: уведомления, заполнение наборов, история статусов."""
from django.contrib.auth.models import User
from django.db.models import Count
from django.utils import timezone

from lms.models import UserProfile
from lms.utils import log_activity, notify_user
from .models import GroupSet, StudentApplication, ApplicationStatusHistory

# Пороги заполнения набора для автоуведомлений
FILL_THRESHOLDS = (80, 90, 100)


def staff_users():
    """Пользователи с ролью ресепшен или админ."""
    role_ids = UserProfile.objects.filter(role__in=['reception', 'admin']).values_list('user_id', flat=True)
    return User.objects.filter(id__in=role_ids)


def notify_staff(text, link=''):
    """Внутрисайтовое уведомление всем ресепшенам и админам."""
    for user in staff_users():
        notify_user(user, text, link)


def check_group_set_fill(group_set):
    """Проверяет заполненность набора и шлёт уведомления на порогах 80/90/100%.

    Вызывается после создания заявки или изменения статуса заявки.
    Возвращает список отправленных порогов.
    """
    if not group_set or not group_set.capacity:
        return []
    pct = group_set.fill_percent()
    sent = []
    for threshold in FILL_THRESHOLDS:
        if pct >= threshold:
            flag = f'notified_{threshold}'
            if not getattr(group_set, flag):
                setattr(group_set, flag, True)
                group_set.save(update_fields=[flag])
                try:
                    from core.telegram_utils import notify_group_fill
                    notify_group_fill(group_set, threshold)
                except Exception:
                    pass
                from django.urls import reverse
                notify_staff(
                    f'Набор «{group_set.name}» заполнен на {threshold}% '
                    f'({group_set.reserved_count()}/{group_set.capacity}).',
                    reverse('applications:set_detail', kwargs={'pk': group_set.pk}),
                )
                sent.append(threshold)
    return sent


def create_application_status_history(application, old_status, new_status,
                                      user=None, note=''):
    """Пишет запись в историю статусов заявки."""
    ApplicationStatusHistory.objects.create(
        application=application,
        old_status=old_status,
        new_status=new_status,
        changed_by=user,
        note=note,
    )


def set_application_status(application, new_status, user=None, note=''):
    """Меняет статус заявки с журналированием."""
    old_status = application.status
    if old_status == new_status:
        return False
    application.status = new_status
    application.updated_by = user
    application.status_changed_at = timezone.now()
    application.save(update_fields=['status', 'updated_by', 'status_changed_at'])
    create_application_status_history(application, old_status, new_status, user, note)
    if user:
        log_activity(user, f'Сменил статус заявки: {application.name}',
                     target=application.name,
                     details=f'{old_status} → {new_status}' + (f' ({note})' if note else ''))
    if application.group_set:
        check_group_set_fill(application.group_set)
    return True
