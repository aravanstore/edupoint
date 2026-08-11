# -*- coding: utf-8 -*-
"""Догружает данные об оплате («день оплаты» из Excel) для УЖЕ импортированных
учеников. Не создаёт новых пользователей/групп — только Payment + PaymentExtension.

«День оплаты» = дата последней оплаты ученика (подтверждено владельцем сайта).
Из неё считается: Payment за тот месяц (подтверждена) + PaymentExtension на
текущий месяц с новым сроком = дата_оплаты + 1 месяц (плавающий цикл, а не
календарный).

Запуск:
    python import_payments.py --dry-run
    python import_payments.py --commit
"""
import os
import sys
import argparse
import calendar
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edupoint.settings')

env_path = os.path.join(BASE, 'deploy.env')
if os.path.exists(env_path):
    with open(env_path, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

import django
django.setup()

sys.path.insert(0, BASE)
from import_excel import parse_workbook, CATEGORY_META, parse_time  # noqa: E402
from django.utils import timezone  # noqa: E402
from django.db import transaction  # noqa: E402
from lms.models import Group, StudentProfile, Payment, PaymentExtension  # noqa: E402


def add_month(d):
    if d.month == 12:
        y, m = d.year + 1, 1
    else:
        y, m = d.year, d.month + 1
    last_day = calendar.monthrange(y, m)[1]
    return d.replace(year=y, month=m, day=min(d.day, last_day))


def to_date(raw):
    if raw is None:
        return None
    if isinstance(raw, datetime.datetime):
        return raw.date()
    if isinstance(raw, datetime.date):
        return raw
    return None


def group_name_for(b):
    return (f"{CATEGORY_META[b['category']][0]} — {b['book_label']} — "
            f"{b['teacher']} — Ауд.{b['room']} {b['time'].replace('-', ':')}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--commit', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    blocks = parse_workbook()
    today = timezone.localdate()
    current_month_start = today.replace(day=1)

    matched, no_date, not_found, ambiguous = 0, 0, 0, 0
    plan = []  # (student, pay_date, next_due)

    for b in blocks:
        if not b['students']:
            continue
        gname = group_name_for(b)
        group = Group.objects.filter(name=gname).first()
        if not group:
            print(f'  [!] Группа не найдена: {gname}')
            continue

        for s in b['students']:
            pay_date = to_date(s.get('pay_date_raw'))
            fio = s['fio']
            parts = fio.split()
            if len(parts) >= 2:
                last_name, first_name = parts[0], ' '.join(parts[1:])
            else:
                last_name, first_name = '', parts[0] if parts else ''

            candidates = StudentProfile.objects.filter(
                group=group, user__first_name=first_name.strip(), user__last_name=last_name.strip()
            )
            n = candidates.count()
            if n == 0:
                not_found += 1
                print(f'  [не найден] {fio!r} в группе {gname!r}')
                continue
            if n > 1:
                ambiguous += 1
                print(f'  [неоднозначно, {n} совпадений] {fio!r} в группе {gname!r} — беру первого')

            sp = candidates.first()

            if not pay_date:
                no_date += 1
                continue

            next_due = add_month(pay_date)
            matched += 1
            plan.append((sp, pay_date, next_due))

    print()
    print(f'Совпало: {matched}, без даты оплаты: {no_date}, не найдено: {not_found}, неоднозначно: {ambiguous}')

    if not args.commit:
        print('(предпросмотр — ничего не записано; для реального запуска: --commit)')
        for sp, pay_date, next_due in plan[:15]:
            print(f'  {sp.user.get_full_name()}: оплатил {pay_date} -> след. срок {next_due}')
        return

    with transaction.atomic():
        created_payments = 0
        created_ext = 0
        for sp, pay_date, next_due in plan:
            month = pay_date.replace(day=1)
            amount = sp.book.price_per_month if sp.book else 2500
            payment, was_created = Payment.objects.get_or_create(
                student=sp, month=month,
                defaults={'amount': amount, 'method': 'cash', 'is_confirmed': True,
                          'note': f'Импортировано из Excel (день оплаты: {pay_date})'}
            )
            if was_created:
                created_payments += 1

            ext, was_created = PaymentExtension.objects.get_or_create(
                student=sp, month=current_month_start,
                defaults={'new_due_date': next_due,
                          'reason': f'Импортировано из Excel: последняя оплата {pay_date}'}
            )
            if was_created:
                created_ext += 1

    print(f'Создано Payment: {created_payments}, PaymentExtension: {created_ext}')


if __name__ == '__main__':
    main()
