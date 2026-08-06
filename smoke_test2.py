# -*- coding: utf-8 -*-
"""Интеграционные тесты: действия записываются в журнал и создают уведомления."""
import os
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edupoint.settings')
django.setup()

from django.test import Client
from django.test.utils import override_settings
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User

from lms.models import ActivityLog, Notification, StudentProfile, Homework, Payment, Group

passed = 0
failed = 0


def check(name, cond, extra=''):
    global passed, failed
    if cond:
        passed += 1
        print(f'PASS: {name}')
    else:
        failed += 1
        print(f'FAIL: {name} {extra}')


# ---------------------------------------------------------------------------
# 1. Оплата -> журнал действий + уведомление ученику
# ---------------------------------------------------------------------------
c = Client()
c.login(username='reception', password='reception123')
s1 = User.objects.get(username='student1').student_profile
before = ActivityLog.objects.count()
month = timezone.localdate().replace(day=1)
r = c.post(f'/dashboard/reception/students/{s1.pk}/', {
    'form': 'payment', 'month': month.isoformat(),
    'amount': s1.book.price_per_month if s1.book else 2500,
    'method': 'cash', 'is_confirmed': 'on', 'note': 'test',
})
check('payment POST redirects', r.status_code == 302, f'got {r.status_code}')
new_logs = ActivityLog.objects.filter(user=c._login and User.objects.get(username='reception')).count()
check('activity logged on payment', ActivityLog.objects.count() > before)
check('payment notification for student', Notification.objects.filter(
    user=s1.user, text__contains='Оплата подтверждена').exists())

# ---------------------------------------------------------------------------
# 2. Домашнее задание -> журнал + уведомления группе
# ---------------------------------------------------------------------------
ct = Client()
ct.login(username='teacher1', password='teacher123')
tp = User.objects.get(username='teacher1').teacher_profile
group = Group.objects.filter(teacher=tp.teacher).first()
if group:
    n_before = Notification.objects.filter(user__student_profile__group=group).count()
    r = ct.post('/dashboard/teacher/homework/', {
        'group': group.pk, 'title': 'SmokeTest HW', 'description': 'test',
        'due_date': '', 'video': '', 'photo': '', 'file': '',
    })
    check('homework publish redirects', r.status_code == 302, f'got {r.status_code}')
    check('homework logged', ActivityLog.objects.filter(action='Опубликовал задание', target='SmokeTest HW').exists())
    n_after = Notification.objects.filter(user__student_profile__group=group).count()
    check('notifications created for group students', n_after > n_before, f'{n_before}->{n_after}')
    # чистим тестовое задание
    Homework.objects.filter(title='SmokeTest HW').delete()
else:
    print('SKIP: teacher1 has no groups')

# ---------------------------------------------------------------------------
# 3. Объявление -> уведомления
# ---------------------------------------------------------------------------
r = ct.post('/dashboard/teacher/announcements/', {
    'group': '', 'title': 'SmokeTest Ann', 'text': 'test announcement',
})
check('announcement POST redirects', r.status_code == 302, f'got {r.status_code}')
check('announcement logged', ActivityLog.objects.filter(action='Опубликовал объявление', target='SmokeTest Ann').exists())

# ---------------------------------------------------------------------------
# 4. Лимит группы (capacity)
# ---------------------------------------------------------------------------
if group:
    old_cap = group.capacity
    group.capacity = group.students.count()
    group.save(update_fields=['capacity'])
    try:
        r = c.post('/dashboard/reception/students/add/', {
            'first_name': 'Тест', 'last_name': 'Лимит',
            'group': group.pk, 'book': group.book.pk if group.book else '',
            'book_progress': 0, 'parent': '', 'phone': '+996700000000',
            'birth_date': '', 'notes': '', 'is_active': 'on', 'password': '',
        })
        full_msg = 'заполнена' in r.content.decode('utf-8', 'ignore')
        check('full group blocks new student', full_msg, f'got {r.status_code}')
        created = User.objects.filter(username__icontains='test').exists()
        check('no user created for blocked student', not created)
    finally:
        group.capacity = old_cap
        group.save(update_fields=['capacity'])

# ---------------------------------------------------------------------------
# 5. Заморозка -> авто-восстановление после оплаты
# ---------------------------------------------------------------------------
pays = list(Payment.objects.filter(student=s1, month__year=month.year,
                                   month__month=month.month, is_confirmed=True))
if pays:
    for p in pays:
        p.is_confirmed = False
        p.save(update_fields=['is_confirmed'])
    try:
        s1f = StudentProfile.objects.get(pk=s1.pk)
        frozen_before = s1f.is_frozen()
        for p in pays:
            p.is_confirmed = True
            p.save(update_fields=['is_confirmed'])
        s1f = StudentProfile.objects.get(pk=s1.pk)
        check('student frozen without payment', frozen_before)
        check('auto-restore after payment', not s1f.is_frozen())
    finally:
        for p in pays:
            p.is_confirmed = True
            p.save(update_fields=['is_confirmed'])
else:
    print('SKIP: no payment row for student1')

# ---------------------------------------------------------------------------
# 6. Страницы ошибок рендерят кастомные шаблоны
# ---------------------------------------------------------------------------
with override_settings(DEBUG=False, ALLOWED_HOSTS=['*']):
    c404 = Client()
    r = c404.get('/dashboard/definitely-not-here/')
    check('404 renders custom template', b'404' in r.content and 'Страница не найдена'.encode() in r.content)

    # 403: доступ запрещён
    from django.views.defaults import permission_denied
    from django.test import RequestFactory
    rf = RequestFactory()
    req = rf.get('/x/')
    req.user = User.objects.get(username='student1')
    from django.core.exceptions import PermissionDenied
    resp = permission_denied(req, PermissionDenied())
    body = resp.content
    check('403 renders custom template', b'403' in body and 'Доступ запрещён'.encode() in body)

print(f'\nTotal: {passed} passed, {failed} failed')
if failed:
    raise SystemExit(1)
