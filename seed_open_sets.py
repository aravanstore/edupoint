# -*- coding: utf-8 -*-
"""Одноразовый сид: несколько открытых наборов + тестовые заявки учеников,
чтобы секция "Открытые наборы" на главной не была пустой.
Запуск: python seed_open_sets.py
"""
import os
import random
from datetime import date, timedelta

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

from courses.models import Course
from teachers.models import Teacher
from applications.models import GroupSet, StudentApplication, Branch

branch = Branch.objects.first()

SETS = [
    dict(course_id=1, teacher_name='Нускайым', days='tue,thu,sat',
         start_time='10:00', end_time='11:30', capacity=12,
         start_in_days=21),
    dict(course_id=2, teacher_name='Эльнура Сайпидиновна', days='mon,wed,fri',
         start_time='18:00', end_time='19:30', capacity=10,
         start_in_days=14),
    dict(course_id=3, teacher_name=None, days='tue,thu',
         start_time='15:00', end_time='16:30', capacity=10,
         start_in_days=28),
    dict(course_id=6, teacher_name='Эрмекова Асема', days='tue,thu',
         start_time='17:00', end_time='18:30', capacity=8,
         start_in_days=10),
]

TEST_STUDENTS = [
    ('Айгерим Осмонова', '+996700112233', 'enrolled', 'instagram', 'beginner'),
    ('Данияр Асанов', '+996550223344', 'enrolled', 'referral', 'zero'),
    ('Нурбек Жумабеков', '+996770334455', 'enrolled', 'telegram', 'beginner'),
    ('Айзада Мамбетова', '+996500445566', 'enrolled', 'instagram', 'zero'),
    ('Тимур Абдиев', '+996770556677', 'contacted', 'google', 'elementary'),
    ('Камила Нурлановна', '+996550667788', 'new', 'tiktok', 'zero'),
    ('Эрлан Сатыбалдиев', '+996700778899', 'enrolled', 'referral', 'beginner'),
    ('Munara Beksultan', '+996770889900', 'test', 'instagram', 'zero'),
]

from datetime import time as dtime


def parse_time(s):
    h, m = s.split(':')
    return dtime(int(h), int(m))


created_sets = 0
created_apps = 0

for spec in SETS:
    course = Course.objects.filter(pk=spec['course_id']).first()
    if not course:
        continue
    teacher = Teacher.objects.filter(name=spec['teacher_name']).first() if spec['teacher_name'] else None

    group_set, was_created = GroupSet.objects.get_or_create(
        course=course,
        status='open',
        teacher=teacher,
        defaults=dict(
            days=spec['days'],
            start_time=parse_time(spec['start_time']),
            end_time=parse_time(spec['end_time']),
            start_date=date.today() + timedelta(days=spec['start_in_days']),
            capacity=spec['capacity'],
            branch=branch,
        ),
    )
    if was_created:
        created_sets += 1
        print(f'Создан набор: {group_set.name} (id={group_set.pk})')
    else:
        print(f'Уже есть набор: {group_set.name} (id={group_set.pk})')

    # Несколько тестовых заявок на этот набор
    sample = random.sample(TEST_STUDENTS, k=random.randint(3, 5))
    for name, phone, status, source, level in sample:
        if StudentApplication.objects.filter(group_set=group_set, name=name).exists():
            continue
        StudentApplication.objects.create(
            name=name,
            phone=phone,
            course=course,
            group_set=group_set,
            status=status,
            source=source,
            language_level=level,
        )
        created_apps += 1

print(f'Создано наборов: {created_sets}, заявок: {created_apps}')
