# -*- coding: utf-8 -*-
"""Одноразовый сид: тестовые отзывы о преподавателях (для демонстрации профиля).
Запуск: python seed_teacher_reviews.py
"""
import os

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

from teachers.models import Teacher
from reviews.models import Review

TEST_REVIEWS = [
    ('Айбек Т.', 5, 'Отличный преподаватель, объясняет очень понятно даже сложные темы. Занятия проходят интересно, никогда не скучно!'),
    ('Медина А.', 5, 'Благодаря этому преподавателю я сдала TOPIK с первого раза. Спасибо за терпение и поддержку!'),
    ('Нурлан С.', 4, 'Хорошая подача материала, домашние задания помогают закрепить пройденное. Иногда хочется больше разговорной практики.'),
    ('Жаныл К.', 5, 'Очень доброжелательный и внимательный преподаватель, всегда готов повторить и объяснить ещё раз.'),
]

created = 0
for i, teacher in enumerate(Teacher.objects.filter(is_active=True)):
    pair = [TEST_REVIEWS[i % len(TEST_REVIEWS)], TEST_REVIEWS[(i + 1) % len(TEST_REVIEWS)]]
    for name, rating, text in pair:
        if Review.objects.filter(teacher=teacher, name=name).exists():
            continue
        Review.objects.create(
            name=name,
            teacher=teacher,
            rating=rating,
            text=text,
            is_approved=True,
        )
        created += 1
        print(f'Добавлен отзыв для {teacher.name}: {name} ({rating}⭐)')

print(f'Создано отзывов: {created}')
