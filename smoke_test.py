# -*- coding: utf-8 -*-
"""Smoke test: авторизация, роли, изоляция, новые страницы."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edupoint.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.test.utils import override_settings

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


c = Client()

# 1. Страница входа
r = c.get('/dashboard/login/')
check('login GET 200', r.status_code == 200, f'got {r.status_code}')

# 2. Неверный логин
r = c.post('/dashboard/login/', {'username': 'nobody', 'password': 'wrong'})
check('wrong login 200 (no redirect)', r.status_code == 200, f'got {r.status_code}')
check('wrong login error msg', 'Неверный логин или пароль' in r.content.decode('utf-8', 'ignore'))
check('wrong login no session cookie', 'sessionid' not in c.cookies)

# 3. Верный вход студента
c = Client()
r = c.post('/dashboard/login/', {'username': 'student1', 'password': 'student123'}, follow=True)
check('student login lands on student dashboard', r.status_code == 200 and any(
    '/dashboard/student/' in u for u, _ in r.redirect_chain), f'chain={r.redirect_chain}')
check('student dashboard content', 'student' in str(r.content).lower())

# 4. Remember me -> cookie Max-Age = 30 дней
cR = Client()
r = cR.post('/dashboard/login/', {'username': 'student1', 'password': 'student123', 'remember': 'on'})
maxage = r.cookies.get('sessionid').get('max-age')
check('remember max-age ~30d', maxage is not None and int(maxage) == 60 * 60 * 24 * 30, f'max-age={maxage}')
# без remember -> сессионная cookie (браузерная сессия, max-age отсутствует)
cN = Client()
r = cN.post('/dashboard/login/', {'username': 'student1', 'password': 'student123'})
nmax = r.cookies.get('sessionid').get('max-age')
check('no-remember browser session (no max-age)', not nmax, f'max-age={nmax}')

# 5. Логаут -> редирект на логин, «Назад» не даёт кабинет (no-cache)
r = c.get('/dashboard/logout/')
check('logout redirect', r.status_code == 302 and '/dashboard/login/' in r.url)
check('no-cache header after logout', r.get('Cache-Control') and 'no-store' in r.get('Cache-Control', ''))

# 6. Роль-изоляция: студент не может открыть ресепшен
c3 = Client()
c3.login(username='student1', password='student123')
r = c3.get('/dashboard/reception/students/')
check('student blocked from reception (redirect)', r.status_code == 302)
check('no-cache on cabinet', r.get('Cache-Control') and 'no-store' in r.get('Cache-Control', ''))

# 7. Заморозка: временно снимаем оплату за текущий месяц (восстанавливаем в finally)
from lms.models import Payment
from django.utils import timezone as _tz
s1 = User.objects.get(username='student1').student_profile
month = _tz.localdate().replace(day=1)
pay_qs = Payment.objects.filter(student=s1, month__year=month.year, month__month=month.month, is_confirmed=True)
ids = list(pay_qs.values_list('id', flat=True))
pay_qs.update(is_confirmed=False)
try:
    c4 = Client()
    c4.login(username='student1', password='student123')
    r = c4.get('/dashboard/student/')
    check('frozen student dashboard 200', r.status_code == 200)
    check('frozen banner shown', 'неоплаты' in r.content.decode('utf-8', 'ignore'))
    r = c4.get('/dashboard/student/homework/1/submit/')
    check('frozen student cannot submit homework (redirect)', r.status_code == 302)
finally:
    Payment.objects.filter(id__in=ids).update(is_confirmed=True)

# 8. Ресепшен
c5 = Client()
c5.login(username='reception', password='reception123')
r = c5.get('/dashboard/reception/')
check('reception dashboard 200', r.status_code == 200, f'got {r.status_code}')
r = c5.get('/dashboard/reception/students/')
check('reception students 200', r.status_code == 200, f'got {r.status_code}')
r = c5.get('/dashboard/reception/students/add/')
check('reception add student 200', r.status_code == 200, f'got {r.status_code}')
r = c5.get('/dashboard/admin/analytics/')
check('analytics 200', r.status_code == 200, f'got {r.status_code}')
r = c5.get('/dashboard/admin/activity/')
check('activity log 200', r.status_code == 200, f'got {r.status_code}')
r = c5.get('/dashboard/notifications/')
check('notifications 200', r.status_code == 200, f'got {r.status_code}')

# 9. Учитель
c6 = Client()
c6.login(username='teacher1', password='teacher123')
r = c6.get('/dashboard/teacher/')
check('teacher dashboard 200', r.status_code == 200, f'got {r.status_code}')
r = c6.get('/dashboard/teacher/journal/1/')
check('teacher journal 200', r.status_code == 200, f'got {r.status_code}')
r = c6.get('/dashboard/teacher/homework/')
check('teacher homework 200', r.status_code == 200, f'got {r.status_code}')

# 10. Родитель
c7 = Client()
c7.login(username='parent1', password='parent123')
r = c7.get('/dashboard/parent/')
check('parent dashboard 200', r.status_code == 200, f'got {r.status_code}')

# 11. Админ -> /admin/
c8 = Client()
c8.login(username='admin', password='admin12345')
r = c8.get('/dashboard/')
check('admin dashboard redirects to /admin/', r.status_code == 302 and r.url.startswith('/admin/'), f'url={r.url}')

# 12. 404 страница (DEBUG=False)
with override_settings(DEBUG=False, ALLOWED_HOSTS=['*']):
    c9 = Client()
    r = c9.get('/dashboard/no-such-page-xyz/')
    check('404 handler', r.status_code == 404)

# 13. Проверка next-параметра (open redirect защита)
r = c9.post('/dashboard/login/', {'username': 'student1', 'password': 'student123', 'next': 'https://evil.example.com'})
check('open redirect blocked', not r.url.startswith('https://evil.example.com'), f'url={r.url}')

print(f'\nTotal: {passed} passed, {failed} failed')
if failed:
    raise SystemExit(1)
