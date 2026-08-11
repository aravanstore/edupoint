# -*- coding: utf-8 -*-
"""Прогоняет все публичные страницы через Django test Client на всех 4 языках,
чтобы поймать TemplateSyntaxError и другие 500-ки после массового добавления
{% trans %} по 20+ шаблонам. Запуск: python smoke_test_i18n.py
"""
import os
import traceback

BASE = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE, 'deploy.env')
if os.path.exists(env_path):
    with open(env_path, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edupoint.settings')
import django
django.setup()

from django.test import Client
from courses.models import Course
from news.models import NewsPost
from teachers.models import Teacher

client = Client(SERVER_NAME='edupoint.aravan.kg')

course = Course.objects.filter(is_active=True).first()
news = NewsPost.objects.filter(is_published=True).first()
teacher = Teacher.objects.filter(is_active=True).first()

urls = [
    '/',
    '/about/',
    '/gallery/',
    '/contact/',
    '/search/?q=korean',
    '/courses/',
    '/courses/lang/korean/',
    '/courses/lang/english/',
    '/courses/lang/german/',
    '/courses/lang/chinese/',
    '/teachers/',
    '/exams/',
    '/exams/topik/',
    '/exams/ielts/',
    '/exams/goethe/',
    '/news/',
    '/reviews/',
    '/apply/',
]
if course:
    urls.append(f'/courses/{course.slug}/')
if news:
    urls.append(f'/news/{news.slug}/')
if teacher:
    urls.append(f'/teachers/{teacher.pk}/')

langs = ['ru', 'de', 'ko', 'zh-hans']

total = 0
failed = 0
for lang in langs:
    for url in urls:
        total += 1
        try:
            resp = client.get(url, HTTP_ACCEPT_LANGUAGE=lang, secure=True)
            if resp.status_code >= 500:
                failed += 1
                print(f'[FAIL {resp.status_code}] lang={lang} {url}')
                try:
                    print('   ', str(resp.content[:300]))
                except Exception:
                    pass
            elif resp.status_code not in (200, 302):
                print(f'[WARN {resp.status_code}] lang={lang} {url}')
        except Exception as e:
            failed += 1
            print(f'[EXCEPTION] lang={lang} {url}: {e}')
            traceback.print_exc()

print(f'\nВсего проверок: {total}, ошибок: {failed}')
