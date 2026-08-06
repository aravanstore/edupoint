"""Заполняет платформу LMS демонстрационными данными.

Использование:
    python manage.py seed_lms
"""
import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone

from courses.models import Category, Course
from teachers.models import Teacher
from lms.models import (
    UserProfile, Book, Group, StudentProfile, ParentProfile, TeacherProfile,
    Grade, Attendance, Homework, HomeworkSubmission, Payment,
    PaymentExtension, Announcement,
)

STUDENT_PASSWORD = 'student123'
TEACHER_PASSWORD = 'teacher123'
PARENT_PASSWORD = 'parent123'
RECEPTION_PASSWORD = 'reception123'

GRADES_POOL = [5, 6, 6, 7, 7, 8, 8, 8, 9, 9, 10]
ATT_POOL = ['present', 'present', 'present', 'late', 'absent']


class Command(BaseCommand):
    help = 'Заполняет LMS демо-данными (книги, группы, аккаунты, оценки, оплаты).'

    def handle(self, *args, **options):
        today = timezone.localdate()
        month_start = today.replace(day=1)

        # ------------------------------------------------------------------
        # Ресепшен
        # ------------------------------------------------------------------
        rec_user, _ = User.objects.get_or_create(username='reception', defaults={
            'first_name': 'Ресепшен', 'is_staff': False,
        })
        rec_user.set_password(RECEPTION_PASSWORD)
        rec_user.save()
        UserProfile.objects.update_or_create(user=rec_user, defaults={'role': 'reception', 'phone': '+996 700 995 577'})

        # ------------------------------------------------------------------
        # Книги (корейский — 6 книг, остальные — по 6)
        # ------------------------------------------------------------------
        books_by_category = {}
        for cat in Category.objects.all():
            books = []
            for i in range(1, 7):
                book, _ = Book.objects.get_or_create(
                    category=cat, order=i,
                    defaults={
                        'name': f'{cat.name} — Book {i}',
                        'duration_months': 2,
                        'price_per_month': 2500,
                        'is_active': True,
                    },
                )
                books.append(book)
            books_by_category[cat] = books

        # ------------------------------------------------------------------
        # Учителя
        # ------------------------------------------------------------------
        teachers = list(Teacher.objects.all())
        teacher_links = {}
        for i, teacher in enumerate(teachers[:3], start=1):
            u, _ = User.objects.get_or_create(username=f'teacher{i}', defaults={
                'first_name': teacher.name.split()[0] if teacher.name.split() else teacher.name,
            })
            u.set_password(TEACHER_PASSWORD)
            u.save()
            UserProfile.objects.update_or_create(user=u, defaults={'role': 'teacher', 'phone': '+996 700 000 00%d' % i})
            TeacherProfile.objects.update_or_create(user=u, defaults={'teacher': teacher})
            teacher.user = u
            teacher.save()
            teacher_links[i] = teacher

        korean_cat = Category.objects.filter(language_code='korean').first()
        korean_course = Course.objects.filter(category=korean_cat, is_active=True).first() if korean_cat else None
        other_course = Course.objects.exclude(category=korean_cat).filter(is_active=True).first()

        # ------------------------------------------------------------------
        # Группы
        # ------------------------------------------------------------------
        groups = {}
        g1, _ = Group.objects.get_or_create(
            name='Korean Book 1 — 14:00',
            defaults={
                'course': korean_course, 'teacher': teacher_links.get(1),
                'book': books_by_category[korean_cat][0] if korean_cat else None,
                'days': 'mon,wed,fri', 'start_time': '14:00', 'end_time': '15:00',
                'room': '101', 'capacity': 10, 'status': 'active', 'started_at': today - timedelta(days=90),
            },
        )
        groups[1] = g1
        g2, _ = Group.objects.get_or_create(
            name='Korean Book 2 — 16:00',
            defaults={
                'course': korean_course, 'teacher': teacher_links.get(2),
                'book': books_by_category[korean_cat][1] if korean_cat else None,
                'days': 'tue,thu', 'start_time': '16:00', 'end_time': '17:00',
                'room': '102', 'capacity': 8, 'status': 'active', 'started_at': today - timedelta(days=30),
            },
        )
        groups[2] = g2

        # ------------------------------------------------------------------
        # Родители
        # ------------------------------------------------------------------
        parents = {}
        for i, (name, login) in enumerate([('Айгуль', 'parent1'), ('Бакыт', 'parent2')], start=1):
            u, _ = User.objects.get_or_create(username=login, defaults={'first_name': name})
            u.set_password(PARENT_PASSWORD)
            u.save()
            UserProfile.objects.update_or_create(user=u, defaults={'role': 'parent'})
            p, _ = ParentProfile.objects.get_or_create(user=u, defaults={'phone': f'+996 700 111 00{i}'})
            parents[i] = p

        # ------------------------------------------------------------------
        # Ученики
        # ------------------------------------------------------------------
        students_data = [
            ('Айбек', 'Абдыкадыров', 1, 1, 1, 100),
            ('Мээрим', 'Жумабаева', 1, 1, 1, 40),
            ('Данияр', 'Сатыбалдиев', 1, 2, 1, 0),
            ('Алина', 'Ким', 2, 2, 2, 15),
            ('Эрлан', 'Усенов', 1, 1, 2, 80),
            ('Жанна', 'Пак', 2, 2, None, 5),
            ('Тимур', 'Исмаилов', 1, 1, None, 60),
            ('Сезим', 'Токтосунова', 2, 2, None, 30),
        ]
        students = []
        for i, (first, last, g_key, book_idx, parent_key, progress) in enumerate(students_data, start=1):
            u, _ = User.objects.get_or_create(username=f'student{i}', defaults={
                'first_name': first, 'last_name': last,
            })
            u.set_password(STUDENT_PASSWORD)
            u.save()
            UserProfile.objects.update_or_create(user=u, defaults={'role': 'student'})
            group = groups[g_key]
            book = books_by_category[korean_cat][book_idx - 1] if korean_cat else None
            parent = parents.get(parent_key)
            student, _ = StudentProfile.objects.get_or_create(
                user=u,
                defaults={
                    'group': group, 'book': book, 'book_progress': progress,
                    'parent': parent, 'phone': f'+996 770 000 00{i}',
                    'birth_date': today - timedelta(days=random.randint(3000, 8000)),
                    'is_active': True,
                },
            )
            students.append(student)

        # ------------------------------------------------------------------
        # Оплаты: история за 2 месяца + текущий месяц (кроме «замороженных»)
        # ------------------------------------------------------------------
        frozen_idx = {3, 7}  # Данияр, Тимур — не оплатили текущий месяц
        for idx, s in enumerate(students, start=1):
            for back in (2, 1):
                month = (month_start - timedelta(days=1)).replace(day=1) - timedelta(days=30 * back)
                Payment.objects.update_or_create(
                    student=s, month=month.replace(day=1),
                    defaults={'amount': s.book.price_per_month if s.book else 2500,
                              'method': 'cash', 'is_confirmed': True},
                )
            if idx in frozen_idx:
                continue
            Payment.objects.update_or_create(
                student=s, month=month_start,
                defaults={'amount': s.book.price_per_month if s.book else 2500,
                          'method': 'cash', 'is_confirmed': True},
            )

        # Отсрочка для замороженного ученика Данияра (student3) — пока не активна
        PaymentExtension.objects.get_or_create(
            student=students[2], month=month_start,
            defaults={'new_due_date': month_start + timedelta(days=5), 'reason': 'Тестовая отсрочка'},
        )

        # ------------------------------------------------------------------
        # Оценки и посещаемость за прошлые занятия
        # ------------------------------------------------------------------
        random.seed(42)
        for s in students:
            group = s.group
            for back in range(4, 0, -1):
                day = today - timedelta(days=back)
                if day.weekday() > 5:
                    continue
                if random.random() < 0.85:
                    Grade.objects.get_or_create(
                        student=s, date=day,
                        defaults={'group': group, 'teacher': group.teacher if group else None,
                                  'value': random.choice(GRADES_POOL),
                                  'comment': random.choice(['', '', '', 'Молодец!', 'Есть прогресс', 'Старайся больше'])},
                    )
                Attendance.objects.update_or_create(
                    student=s, date=day,
                    defaults={'group': group, 'status': random.choice(ATT_POOL)},
                )

        # ------------------------------------------------------------------
        # Домашние задания + ответы
        # ------------------------------------------------------------------
        hw1, _ = Homework.objects.get_or_create(
            group=groups[1], title='Изучить грамматику — урок 5',
            defaults={
                'teacher': groups[1].teacher,
                'description': 'Повторить правило частиц 은/는 и выполнить упражнения 1-3 на стр. 42.',
                'due_date': today + timedelta(days=2),
            },
        )
        hw2, _ = Homework.objects.get_or_create(
            group=groups[1], title='Новые слова — тема «Еда»',
            defaults={
                'teacher': groups[1].teacher,
                'description': 'Выучить 20 слов по теме «Еда» и составить 5 предложений.',
                'due_date': today + timedelta(days=4),
            },
        )
        hw3, _ = Homework.objects.get_or_create(
            group=groups[2], title='Аудирование — диалог 1',
            defaults={
                'teacher': groups[2].teacher,
                'description': 'Прослушать диалог и ответить на вопросы письменно.',
                'video': 'https://www.youtube.com/watch?v=example',
                'due_date': today + timedelta(days=3),
            },
        )
        for s in students[:4]:
            if random.random() < 0.6:
                HomeworkSubmission.objects.get_or_create(
                    homework=random.choice([hw1, hw2, hw3]),
                    student=s,
                    defaults={'text': 'Задание выполнено. Спасибо!'},
                )

        # ------------------------------------------------------------------
        # Объявления
        # ------------------------------------------------------------------
        Announcement.objects.get_or_create(
            group=groups[1], title='Завтра занятия отменяются',
            defaults={'author': teacher_links[1].user if teacher_links.get(1) else rec_user,
                      'text': 'По техническим причинам занятие 14:00 переносится на среду в то же время.'},
        )
        Announcement.objects.get_or_create(
            group=groups[2], title='Перенос занятия',
            defaults={'author': teacher_links[2].user if teacher_links.get(2) else rec_user,
                      'text': 'Занятие в четверг начнётся в 16:30.'},
        )

        # ------------------------------------------------------------------
        # Админ (разработчик)
        # ------------------------------------------------------------------
        admin = User.objects.filter(is_superuser=True).first()
        if admin:
            admin.set_password('admin12345')
            admin.is_active = True
            admin.save()
            UserProfile.objects.update_or_create(user=admin, defaults={'role': 'admin'})

        self.stdout.write(self.style.SUCCESS('\n=== LMS заполнена демо-данными ==='))
        self.stdout.write(f'Книг: {Book.objects.count()}, Групп: {Group.objects.count()}, '
                          f'Учеников: {StudentProfile.objects.count()}')
        self.stdout.write(self.style.SUCCESS('\n=== Демо-аккаунты ==='))
        self.stdout.write(f'Ресепшен:    логин reception / {RECEPTION_PASSWORD}')
        for i in (1, 2):
            self.stdout.write(f'Учитель {i}: логин teacher{i} / {TEACHER_PASSWORD}')
        for i, s in enumerate(students, start=1):
            self.stdout.write(f'Ученик {i}:  логин student{i} / {STUDENT_PASSWORD}  ({s}, группа: {s.group.name if s.group else "—"})')
        for i in (1, 2):
            self.stdout.write(f'Родитель {i}: логин parent{i} / {PARENT_PASSWORD}')
        self.stdout.write(self.style.WARNING('\nЗаморожены (неоплата): Данияр (student3), Тимур (student7)'))
        self.stdout.write(self.style.SUCCESS('Админ (разработчик): admin / admin12345 — через /admin/'))
