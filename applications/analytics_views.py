"""Аналитика: дашборд, курсы, преподаватели, посещаемость, финансы, маркетинг."""
import calendar
import datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import render
from django.utils import timezone

from lms.models import StudentProfile, Group, Grade, Attendance, Payment, Book
from lms.views import role_required
from courses.models import Course
from teachers.models import Teacher
from reviews.models import Review

from .models import (StudentApplication, GroupSet, WaitlistEntry,
                     SpendEntry, Branch)
from .export import excel_response, pdf_response

# Порог пропусков подряд для "риска отчисления" (более 3 занятий подряд)
AT_RISK_STREAK = 4

ACTIVE_STATUSES = StudentApplication.ACTIVE_STATUSES


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------
def _last_book_ids():
    """{category_id: id последней активной книги}."""
    books = Book.objects.filter(is_active=True).order_by('category_id', '-order')
    return {b.category_id: b.id for b in books}


def _is_finished(student, last_map):
    book = student.book
    if not book or not book.category_id:
        return False
    return last_map.get(book.category_id) == book.id and (student.book_progress or 0) >= 100


def _student_stats(students, last_map):
    students = list(students)
    total = len(students)
    active = sum(1 for s in students if s.is_active)
    finished = sum(1 for s in students if _is_finished(s, last_map))
    drop = max(total - active - finished, 0)
    return total, active, finished, drop


def _revenue_by_month(n=12):
    today = timezone.localdate()
    months = []
    y, m = today.year, today.month
    for _ in range(n):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    months.reverse()
    rows = []
    for y, m in months:
        total = Payment.objects.filter(is_confirmed=True, month__year=y, month__month=m) \
            .aggregate(t=Sum('amount'))['t'] or 0
        rows.append({'label': f'{m:02d}.{y}', 'year': y, 'month': m, 'total': int(total)})
    return rows


def _applications_by_day(days=30):
    today = timezone.localdate()
    start = today - datetime.timedelta(days=days - 1)
    rows = []
    d = start
    while d <= today:
        rows.append({'date': d.isoformat(), 'count':
                     StudentApplication.objects.filter(created_at__date=d).count()})
        d += datetime.timedelta(days=1)
    return rows


def _attendance_by_day(days=30):
    today = timezone.localdate()
    start = today - datetime.timedelta(days=days - 1)
    qs = Attendance.objects.filter(date__gte=start) \
        .values('date', 'status').annotate(c=Count('id'))
    by_date = {}
    for row in qs:
        by_date.setdefault(row['date'], {})[row['status']] = row['c']
    rows = []
    d = start
    while d <= today:
        dmap = by_date.get(d, {})
        rows.append({
            'date': d.isoformat(),
            'present': dmap.get('present', 0),
            'absent': dmap.get('absent', 0),
            'late': dmap.get('late', 0),
        })
        d += datetime.timedelta(days=1)
    return rows


def _at_risk_students(threshold=AT_RISK_STREAK):
    students = StudentProfile.objects.filter(is_active=True, group__isnull=False) \
        .select_related('user', 'group', 'group__teacher') \
        .prefetch_related('attendance_records')
    result = []
    for s in students:
        records = list(s.attendance_records.order_by('date'))
        streak = 0
        for r in reversed(records):
            if r.status == 'absent':
                streak += 1
            else:
                break
        if streak >= threshold:
            result.append({'student': s, 'streak': streak})
    result.sort(key=lambda x: -x['streak'])
    return result


# ---------------------------------------------------------------------------
# Дашборд
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def analytics_dashboard(request):
    today = timezone.localdate()
    week_start = today - datetime.timedelta(days=6)
    month_start = today.replace(day=1)

    apps = StudentApplication.objects
    total_apps = apps.count()
    enrolled = apps.filter(status='enrolled').count()

    last_map = _last_book_ids()
    all_students = list(StudentProfile.objects.select_related('book').all())
    total, active, finished, _ = _student_stats(all_students, last_map)
    new_students = StudentProfile.objects.filter(enrolled_at__gte=month_start).count()

    revenue_total = Payment.objects.filter(is_confirmed=True).aggregate(t=Sum('amount'))['t'] or 0
    revenue_by_month = _revenue_by_month(12)

    open_groups = Group.objects.filter(status='active')
    filled = [(g.students.count() / g.capacity) * 100 for g in open_groups if g.capacity]
    avg_fill = round(sum(filled) / len(filled), 1) if filled else 0

    conversion = round(enrolled / total_apps * 100) if total_apps else 0

    context = {
        'today': today,
        'apps_today': apps.filter(created_at__date=today).count(),
        'apps_week': apps.filter(created_at__date__gte=week_start).count(),
        'apps_month': apps.filter(created_at__date__gte=month_start).count(),
        'new_students': new_students,
        'active_students': active,
        'finished_students': finished,
        'revenue_total': int(revenue_total),
        'revenue_month': int(Payment.objects.filter(is_confirmed=True, month__year=today.year,
                                                    month__month=today.month)
                             .aggregate(t=Sum('amount'))['t'] or 0),
        'open_groups': open_groups.count(),
        'avg_fill': avg_fill,
        'conversion': conversion,
        'total_apps': total_apps,
        'enrolled': enrolled,
        'revenue_by_month': revenue_by_month,
        'apps_by_day': _applications_by_day(30),
        'status_rows': [(code, label, apps.filter(status=code).count())
                        for code, label in StudentApplication.STATUS_CHOICES],
        'status_choices': StudentApplication.STATUS_CHOICES,
        'active_section': 'analytics',
        'analytics_tab': 'dashboard',
        'page_title': 'Аналитика: дашборд — Edu Point',
    }
    return render(request, 'applications/analytics/dashboard.html', context)


# ---------------------------------------------------------------------------
# По курсам
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def analytics_courses(request):
    last_map = _last_book_ids()
    rows = []
    for course in Course.objects.filter(is_active=True).order_by('category__order', 'name'):
        group_ids = list(course.lms_groups.values_list('id', flat=True))
        students = list(StudentProfile.objects.filter(group_id__in=group_ids)
                        .select_related('book', 'group'))
        total, active, finished, drop = _student_stats(students, last_map)
        student_ids = [s.id for s in students]
        revenue = Payment.objects.filter(is_confirmed=True, student_id__in=student_ids) \
            .aggregate(t=Sum('amount'))['t'] or 0
        reviews = Review.objects.filter(course=course)
        rev_avg = reviews.aggregate(a=Avg('rating'))['a']
        rows.append({
            'course': course,
            'apps': course.applications.count(),
            'total': total,
            'active': active,
            'finished': finished,
            'drop': drop,
            'retention': round(active / total * 100) if total else 0,
            'dropout': round(drop / total * 100) if total else 0,
            'rating': round(rev_avg, 1) if rev_avg else None,
            'reviews': reviews.count(),
            'revenue': int(revenue),
            'profit': int(revenue),
        })
    total_revenue = sum(r['revenue'] for r in rows)
    context = {
        'rows': rows,
        'total_revenue': total_revenue,
        'active_section': 'analytics',
        'analytics_tab': 'courses',
        'page_title': 'Аналитика по курсам — Edu Point',
    }
    return render(request, 'applications/analytics/courses.html', context)


# ---------------------------------------------------------------------------
# По преподавателям
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def analytics_teachers(request):
    last_map = _last_book_ids()
    rows = []
    for teacher in Teacher.objects.filter(is_active=True).order_by('name'):
        group_ids = list(teacher.lms_groups.values_list('id', flat=True))
        students = list(StudentProfile.objects.filter(group_id__in=group_ids)
                        .select_related('book'))
        total, active, finished, _ = _student_stats(students, last_map)
        student_ids = [s.id for s in students]

        att = Attendance.objects.filter(student_id__in=student_ids)
        att_total = att.count()
        att_present = att.filter(status='present').count()
        att_late = att.filter(status='late').count()
        att_percent = round((att_present + att_late) / att_total * 100) if att_total else None

        avg_grade = Grade.objects.filter(student_id__in=student_ids).aggregate(a=Avg('value'))['a']
        reviews = Review.objects.filter(course__in=teacher.courses.all())
        rev_avg = reviews.aggregate(a=Avg('rating'))['a']
        revenue = Payment.objects.filter(is_confirmed=True, student_id__in=student_ids) \
            .aggregate(t=Sum('amount'))['t'] or 0

        rows.append({
            'teacher': teacher,
            'groups': len(group_ids),
            'total': total,
            'finished': finished,
            'att_percent': att_percent,
            'avg_grade': round(avg_grade, 1) if avg_grade else None,
            'reviews': reviews.count(),
            'rating': round(rev_avg, 1) if rev_avg else None,
            'success': round(finished / total * 100) if total else 0,
            'revenue': int(revenue),
        })
    context = {
        'rows': rows,
        'active_section': 'analytics',
        'analytics_tab': 'teachers',
        'page_title': 'Аналитика по преподавателям — Edu Point',
    }
    return render(request, 'applications/analytics/teachers.html', context)


# ---------------------------------------------------------------------------
# Посещаемость
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def analytics_attendance(request):
    by_day = _attendance_by_day(30)
    at_risk = _at_risk_students()

    by_group = []
    for g in Group.objects.filter(status='active').annotate(
            c=Count('attendance_records')):
        att = g.attendance_records
        total = att.count()
        present = att.filter(status='present').count()
        late = att.filter(status='late').count()
        absent = att.filter(status='absent').count()
        percent = round((present + late) / total * 100) if total else 0
        by_group.append({'group': g, 'total': total, 'present': present,
                         'late': late, 'absent': absent, 'percent': percent})

    by_teacher = []
    for teacher in Teacher.objects.filter(lms_groups__isnull=False).distinct():
        group_ids = list(teacher.lms_groups.values_list('id', flat=True))
        att = Attendance.objects.filter(group_id__in=group_ids)
        total = att.count()
        present = att.filter(status='present').count()
        late = att.filter(status='late').count()
        percent = round((present + late) / total * 100) if total else 0
        by_teacher.append({'teacher': teacher, 'total': total, 'present': present,
                           'late': late, 'percent': percent})

    context = {
        'by_day': by_day,
        'by_group': by_group,
        'by_teacher': by_teacher,
        'at_risk': at_risk,
        'at_risk_threshold': AT_RISK_STREAK,
        'active_section': 'analytics',
        'analytics_tab': 'attendance',
        'page_title': 'Аналитика посещаемости — Edu Point',
    }
    return render(request, 'applications/analytics/attendance.html', context)


# ---------------------------------------------------------------------------
# Финансы
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def analytics_financial(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    month_end = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    revenue_by_month = _revenue_by_month(12)

    all_students = list(StudentProfile.objects.select_related('book').all())
    frozen = [s for s in all_students if s.is_frozen()]
    debts = sum(s.debt_amount() for s in frozen)
    pending = [s for s in all_students if s.payment_status()[0] == 'pending']
    expected = sum(s.book.price_per_month if s.book else 2500 for s in pending)

    paid = Payment.objects.filter(is_confirmed=True)
    paid_invoices = paid.filter(month__gte=month_start, month__lte=month_end).count()
    avg_check = paid.aggregate(a=Avg('amount'))['a'] or 0
    ltv = paid.values('student').annotate(t=Sum('amount')).aggregate(a=Avg('t'))['a'] or 0

    by_branch = []
    branches = list(Branch.objects.filter(is_active=True))
    for br in branches:
        ids = list(StudentProfile.objects.filter(group__branch=br).values_list('id', flat=True))
        rev = Payment.objects.filter(is_confirmed=True, student_id__in=ids) \
            .aggregate(t=Sum('amount'))['t'] or 0
        by_branch.append({'name': br.name, 'revenue': int(rev), 'students': len(ids)})
    ids = list(StudentProfile.objects.filter(group__branch__isnull=True).values_list('id', flat=True))
    if ids:
        rev = Payment.objects.filter(is_confirmed=True, student_id__in=ids) \
            .aggregate(t=Sum('amount'))['t'] or 0
        by_branch.append({'name': 'Без филиала', 'revenue': int(rev), 'students': len(ids)})

    by_course = []
    for course in Course.objects.filter(is_active=True):
        ids = list(StudentProfile.objects.filter(group__course=course).values_list('id', flat=True))
        rev = Payment.objects.filter(is_confirmed=True, student_id__in=ids) \
            .aggregate(t=Sum('amount'))['t'] or 0
        by_course.append({'name': course.name, 'revenue': int(rev), 'students': len(ids)})
    by_course.sort(key=lambda x: -x['revenue'])

    by_teacher = []
    for teacher in Teacher.objects.filter(is_active=True):
        ids = list(StudentProfile.objects.filter(group__teacher=teacher).values_list('id', flat=True))
        rev = Payment.objects.filter(is_confirmed=True, student_id__in=ids) \
            .aggregate(t=Sum('amount'))['t'] or 0
        by_teacher.append({'name': teacher.name, 'revenue': int(rev), 'students': len(ids)})
    by_teacher.sort(key=lambda x: -x['revenue'])

    context = {
        'revenue_by_month': revenue_by_month,
        'revenue_total': sum(r['total'] for r in revenue_by_month),
        'debts': int(debts),
        'frozen_count': len(frozen),
        'expected': int(expected),
        'pending_count': len(pending),
        'paid_invoices': paid_invoices,
        'avg_check': int(avg_check),
        'ltv': int(ltv),
        'by_branch': by_branch,
        'by_course': by_course,
        'by_teacher': by_teacher,
        'active_section': 'analytics',
        'analytics_tab': 'financial',
        'page_title': 'Финансовая аналитика — Edu Point',
    }
    return render(request, 'applications/analytics/financial.html', context)


# ---------------------------------------------------------------------------
# Маркетинг
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def analytics_marketing(request):
    rows = []
    for code, label in StudentApplication.SOURCE_CHOICES:
        apps = StudentApplication.objects.filter(source=code)
        leads = apps.count()
        enrolled = apps.filter(status='enrolled').count()
        conv = round(enrolled / leads * 100) if leads else 0
        spend = SpendEntry.objects.filter(source=code).aggregate(t=Sum('amount'))['t'] or 0
        cpl = round(float(spend) / leads, 1) if leads else None
        student_ids = list(apps.exclude(student__isnull=True).values_list('student_id', flat=True))
        revenue = Payment.objects.filter(is_confirmed=True, student_id__in=student_ids) \
            .aggregate(t=Sum('amount'))['t'] or 0
        rows.append({
            'code': code,
            'label': label,
            'leads': leads,
            'enrolled': enrolled,
            'conv': conv,
            'spend': float(spend),
            'cpl': cpl,
            'revenue': int(revenue),
        })
    total_leads = sum(r['leads'] for r in rows)
    total_spend = sum(r['spend'] for r in rows)
    total_revenue = sum(r['revenue'] for r in rows)
    context = {
        'rows': rows,
        'total_leads': total_leads,
        'total_spend': round(total_spend, 1),
        'total_revenue': total_revenue,
        'spend_entries': SpendEntry.objects.order_by('-month', 'source'),
        'active_section': 'analytics',
        'analytics_tab': 'marketing',
        'page_title': 'Маркетинговая аналитика — Edu Point',
    }
    return render(request, 'applications/analytics/marketing.html', context)


# ---------------------------------------------------------------------------
# Экспорт
# ---------------------------------------------------------------------------
def _build_export(section):
    """Возвращает (title, headers, rows)."""
    today = timezone.localdate()
    last_map = _last_book_ids()

    if section == 'dashboard':
        apps = StudentApplication.objects
        revenue_by_month = _revenue_by_month(12)
        headers = ['Показатель', 'Значение']
        rows = [
            ['Заявок за сегодня', apps.filter(created_at__date=today).count()],
            ['Заявок за неделю', apps.filter(created_at__date__gte=today - datetime.timedelta(days=6)).count()],
            ['Заявок за месяц', apps.filter(created_at__date__gte=today.replace(day=1)).count()],
            ['Всего заявок', apps.count()],
            ['Новых учеников (месяц)',
             StudentProfile.objects.filter(enrolled_at__gte=today.replace(day=1)).count()],
            ['Активных учеников', StudentProfile.objects.filter(is_active=True).count()],
            ['Открытых групп', Group.objects.filter(status='active').count()],
            ['Общая выручка', int(Payment.objects.filter(is_confirmed=True).aggregate(t=Sum('amount'))['t'] or 0)],
        ]
        rows.append([])
        rows.append(['Выручка по месяцам', ''])
        for r in revenue_by_month:
            rows.append([f'  {r["label"]}', r['total']])
        return ('Сводный дашборд', headers, rows)

    if section == 'applications':
        headers = ['Дата', 'Имя', 'Телефон', 'Набор', 'Источник', 'Статус']
        rows = [[a.created_at.strftime('%d.%m.%Y %H:%M'), a.name, a.phone,
                 a.group_set.name if a.group_set else '—', a.get_source_display(),
                 a.get_status_display()]
                for a in StudentApplication.objects.select_related('group_set')[:500]]
        return ('Заявки (CRM)', headers, rows)

    if section == 'sets':
        headers = ['Набор', 'Курс', 'Преподаватель', 'Расписание', 'Старт', 'Мест', 'Заявок', 'Статус']
        rows = [[s.name, s.course.name, s.teacher.name if s.teacher else '—',
                 s.schedule_display(), s.start_date.strftime('%d.%m.%Y') if s.start_date else '—',
                 s.capacity or '∞', s.reserved_count(), s.get_status_display()]
                for s in GroupSet.objects.select_related('course', 'teacher')]
        return ('Наборы групп', headers, rows)

    if section == 'courses':
        headers = ['Курс', 'Заявки', 'Студентов', 'Завершили', 'Удержание %', 'Отсев %',
                   'Рейтинг', 'Доход (сом)']
        rows = []
        for course in Course.objects.filter(is_active=True):
            group_ids = list(course.lms_groups.values_list('id', flat=True))
            students = list(StudentProfile.objects.filter(group_id__in=group_ids).select_related('book'))
            total, active, finished, drop = _student_stats(students, last_map)
            student_ids = [s.id for s in students]
            rev = Payment.objects.filter(is_confirmed=True, student_id__in=student_ids) \
                .aggregate(t=Sum('amount'))['t'] or 0
            rev_avg = Review.objects.filter(course=course).aggregate(a=Avg('rating'))['a']
            rows.append([course.name, course.applications.count(), total, finished,
                         round(active / total * 100) if total else 0,
                         round(drop / total * 100) if total else 0,
                         round(rev_avg, 1) if rev_avg else '—', int(rev)])
        return ('Аналитика по курсам', headers, rows)

    if section == 'teachers':
        headers = ['Преподаватель', 'Групп', 'Студентов', 'Посещаемость %', 'Средний балл',
                   'Отзывов', 'Рейтинг', 'Завершили %', 'Доход (сом)']
        rows = []
        for teacher in Teacher.objects.filter(is_active=True):
            group_ids = list(teacher.lms_groups.values_list('id', flat=True))
            students = list(StudentProfile.objects.filter(group_id__in=group_ids).select_related('book'))
            total, active, finished, _ = _student_stats(students, last_map)
            student_ids = [s.id for s in students]
            att = Attendance.objects.filter(student_id__in=student_ids)
            att_total = att.count()
            att_percent = round((att.filter(status='present').count() + att.filter(status='late').count())
                                / att_total * 100) if att_total else '—'
            avg_grade = Grade.objects.filter(student_id__in=student_ids).aggregate(a=Avg('value'))['a']
            reviews = Review.objects.filter(course__in=teacher.courses.all())
            rev_avg = reviews.aggregate(a=Avg('rating'))['a']
            rev = Payment.objects.filter(is_confirmed=True, student_id__in=student_ids) \
                .aggregate(t=Sum('amount'))['t'] or 0
            rows.append([teacher.name, len(group_ids), total, att_percent,
                         round(avg_grade, 1) if avg_grade else '—', reviews.count(),
                         round(rev_avg, 1) if rev_avg else '—',
                         round(finished / total * 100) if total else 0, int(rev)])
        return ('Аналитика по преподавателям', headers, rows)

    if section == 'attendance':
        headers = ['Показатель', 'Значение']
        rows = [['Ученики с риском отчисления (> 3 пропуска подряд)', len(_at_risk_students())]]
        rows.append([])
        rows.append(['Посещаемость по группам', ''])
        for g in Group.objects.filter(status='active'):
            att = g.attendance_records
            total = att.count()
            rows.append([f'  {g.name}',
                         f'{total} занятий, посещаемость {round((att.filter(status="present").count() + att.filter(status="late").count()) / total * 100) if total else 0}%'])
        return ('Аналитика посещаемости', headers, rows)

    if section == 'financial':
        all_students = list(StudentProfile.objects.select_related('book').all())
        frozen = [s for s in all_students if s.is_frozen()]
        pending = [s for s in all_students if s.payment_status()[0] == 'pending']
        paid = Payment.objects.filter(is_confirmed=True)
        headers = ['Показатель', 'Значение']
        rows = [
            ['Общая выручка', int(paid.aggregate(t=Sum('amount'))['t'] or 0)],
            ['Задолженности (сом)', sum(s.debt_amount() for s in frozen)],
            ['Учеников с задолженностью', len(frozen)],
            ['Ожидаемые платежи (сом)', sum(s.book.price_per_month if s.book else 2500 for s in pending)],
            ['Ожидают оплаты', len(pending)],
            ['Оплаченных счетов (месяц)',
             paid.filter(month__year=today.year, month__month=today.month).count()],
            ['Средний чек (сом)', int(paid.aggregate(a=Avg('amount'))['a'] or 0)],
            ['LTV ученика (сом)',
             int(paid.values('student').annotate(t=Sum('amount')).aggregate(a=Avg('t'))['a'] or 0)],
        ]
        rows.append([])
        rows.append(['Выручка по месяцам', ''])
        for r in _revenue_by_month(12):
            rows.append([f'  {r["label"]}', r['total']])
        return ('Финансовая аналитика', headers, rows)

    if section == 'marketing':
        headers = ['Источник', 'Лиды', 'Зачислено', 'Конверсия %', 'Расходы (сом)',
                   'Стоимость лида (сом)', 'Доход (сом)']
        rows = []
        for code, label in StudentApplication.SOURCE_CHOICES:
            apps = StudentApplication.objects.filter(source=code)
            leads = apps.count()
            enrolled = apps.filter(status='enrolled').count()
            spend = SpendEntry.objects.filter(source=code).aggregate(t=Sum('amount'))['t'] or 0
            student_ids = list(apps.exclude(student__isnull=True).values_list('student_id', flat=True))
            rev = Payment.objects.filter(is_confirmed=True, student_id__in=student_ids) \
                .aggregate(t=Sum('amount'))['t'] or 0
            rows.append([label, leads, enrolled,
                         round(enrolled / leads * 100) if leads else 0,
                         float(spend),
                         round(float(spend) / leads, 1) if leads else '—',
                         int(rev)])
        return ('Маркетинговая аналитика', headers, rows)

    return ('Отчёт', ['Показатель'], [])


@login_required
@role_required('reception', 'admin')
def export_view(request):
    section = request.GET.get('section', 'dashboard')
    fmt = request.GET.get('fmt', 'xlsx')
    today = timezone.localdate()
    title, headers, rows = _build_export(section)
    safe_title = ''.join(c for c in title if c.isalnum() or c in ' -').strip()
    stamp = today.strftime('%Y%m%d')
    filename = f'{safe_title}_{stamp}.{fmt}'
    if fmt == 'pdf':
        return pdf_response(title, headers, rows, filename)
    return excel_response(title, headers, rows, filename)
