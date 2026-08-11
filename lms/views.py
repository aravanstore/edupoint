import random
import string

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Count, Q, Avg, Sum as models_sum
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST

from teachers.models import Teacher
from .models import (
    UserProfile, StudentProfile, ParentProfile, TeacherProfile,
    Group, Homework, Payment, PaymentExtension, Announcement, Attendance,
    Notification, ActivityLog, Book, Grade,
)
from .forms import (
    LoginForm, StudentForm, HomeworkForm, SubmissionForm, PaymentForm,
    ExtensionForm, AnnouncementForm, GradeAttendanceForm, ProfileForm, TeacherForm,
)
from .utils import log_request_activity, notify_student, notify_user, bulk_frozen_student_ids, bulk_payment_status

DAY_ORDER = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
DAY_LABELS = {
    'mon': 'Понедельник', 'tue': 'Вторник', 'wed': 'Среда',
    'thu': 'Четверг', 'fri': 'Пятница', 'sat': 'Суббота', 'sun': 'Воскресенье',
}


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------
def role_required(*roles):
    """Декоратор: доступ только пользователям с указанной ролью."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            role = UserProfile.role_for(request.user)
            if role not in roles:
                messages.error(request, 'У вас нет доступа к этому разделу.')
                return redirect('lms:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def _translit(text):
    """Простая транслитерация кириллицы для логинов."""
    if not text:
        return ''
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    result = []
    for ch in text.lower():
        result.append(mapping.get(ch, ch if ch.isalnum() else ''))
    return ''.join(result)


def _generate_username(first_name, last_name, phone):
    base = (_translit(first_name) + '.' + _translit(last_name)).strip('.')
    if not base:
        base = ''.join(ch for ch in (phone or '') if ch.isdigit())
    if not base:
        base = 'student'
    candidate = base
    n = 1
    while User.objects.filter(username=candidate).exists():
        candidate = f'{base}{n}'
        n += 1
    return candidate


def _generate_password():
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(8))


def _safe_next(request):
    """Возвращает безопасный next-параметр (без open redirect)."""
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return ''


# ---------------------------------------------------------------------------
# Аутентификация
# ---------------------------------------------------------------------------
@never_cache
@sensitive_post_parameters('password')
def login_view(request):
    if request.user.is_authenticated:
        return redirect('lms:dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username'].strip()
        password = form.cleaned_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Аккаунт отключён. Обратитесь в учебный центр.')
            else:
                login(request, user)
                # «Запомнить меня»: 30 дней, иначе — до закрытия браузера.
                if form.cleaned_data.get('remember'):
                    request.session.set_expiry(60 * 60 * 24 * 30)
                else:
                    request.session.set_expiry(0)
                next_url = _safe_next(request)
                if next_url:
                    return redirect(next_url)
                return redirect('lms:dashboard')
        else:
            # Сбрасываем возможную чужую/битую сессию и показываем ошибку.
            if 'sessionid' in request.COOKIES:
                request.session.flush()
            messages.error(request, 'Неверный логин или пароль.')
    return render(request, 'lms/login.html', {
        'form': form,
        'page_title': 'Вход — Edu Point LMS',
        'next': request.GET.get('next', ''),
    })


@never_cache
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, 'Вы вышли из системы.')
    return redirect('lms:login')


@never_cache
@login_required
def dashboard(request):
    role = UserProfile.role_for(request.user)
    if role == 'student':
        if hasattr(request.user, 'student_profile'):
            return redirect('lms:student_dashboard')
        messages.error(request, 'Ваш профиль ученика ещё не настроен. Обратитесь к администрации.')
        return redirect('lms:profile')
    if role == 'parent':
        if hasattr(request.user, 'parent_profile'):
            return redirect('lms:parent_dashboard')
        messages.error(request, 'Ваш профиль родителя ещё не настроен. Обратитесь к администрации.')
        return redirect('lms:profile')
    if role == 'teacher':
        if hasattr(request.user, 'teacher_profile'):
            return redirect('lms:teacher_dashboard')
        messages.error(request, 'Ваш профиль учителя ещё не настроен. Обратитесь к администрации.')
        return redirect('lms:profile')
    if role == 'reception':
        return redirect('lms:reception_dashboard')
    return redirect('/admin/')


@login_required
def profile_view(request):
    user = request.user
    phone = ''
    try:
        phone = user.profile.phone
    except UserProfile.DoesNotExist:
        pass

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile':
            form = ProfileForm(request.POST)
            if form.is_valid():
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                user.email = form.cleaned_data['email']
                user.save()
                profile, _ = UserProfile.objects.get_or_create(user=user)
                profile.phone = form.cleaned_data['phone']
                profile.save()
                messages.success(request, 'Профиль обновлён.')
                return redirect('lms:profile')
            messages.error(request, 'Проверьте данные формы.')
        elif action == 'password':
            old = request.POST.get('old_password', '')
            new1 = request.POST.get('new_password1', '')
            new2 = request.POST.get('new_password2', '')
            if not user.check_password(old):
                messages.error(request, 'Текущий пароль неверный.')
            elif len(new1) < 8:
                messages.error(request, 'Новый пароль должен быть не короче 8 символов.')
            elif new1 != new2:
                messages.error(request, 'Новые пароли не совпадают.')
            else:
                user.set_password(new1)
                user.save()
                messages.success(request, 'Пароль изменён. Войдите заново.')
                logout(request)
                return redirect('lms:login')
        return redirect('lms:profile')

    form = ProfileForm(initial={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': phone,
    })
    return render(request, 'lms/profile.html', {
        'form': form,
        'active_section': 'profile',
        'page_title': 'Мой профиль — Edu Point',
    })


# ---------------------------------------------------------------------------
# Кабинет ученика
# ---------------------------------------------------------------------------
def _get_student_or_redirect(request):
    try:
        return request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Профиль ученика не найден.')
        return None


@login_required
@role_required('student')
def student_dashboard(request):
    student = _get_student_or_redirect(request)
    if not student:
        return redirect('lms:dashboard')

    context = {
        'student': student,
        'frozen': student.is_frozen(),
        'pay_status': student.payment_status(),
        'average': student.average_grade(),
        'attendance': student.attendance_stats(),
        'active_section': 'overview',
        'page_title': f'Кабинет ученика — {student} — Edu Point',
    }
    return render(request, 'lms/student/dashboard.html', context)


@login_required
@role_required('student')
def student_grades(request):
    student = _get_student_or_redirect(request)
    if not student:
        return redirect('lms:dashboard')
    grades = student.grades.select_related('group', 'teacher').order_by('-date', '-created_at')
    return render(request, 'lms/student/grades.html', {
        'student': student,
        'frozen': student.is_frozen(),
        'grades': grades,
        'average': student.average_grade(),
        'active_section': 'grades',
        'page_title': 'Оценки — Edu Point',
    })


@login_required
@role_required('student')
def student_attendance(request):
    student = _get_student_or_redirect(request)
    if not student:
        return redirect('lms:dashboard')
    records = student.attendance_records.select_related('group').order_by('-date')
    return render(request, 'lms/student/attendance.html', {
        'student': student,
        'frozen': student.is_frozen(),
        'records': records,
        'stats': student.attendance_stats(),
        'active_section': 'attendance',
        'page_title': 'Посещаемость — Edu Point',
    })


@login_required
@role_required('student')
def student_homework(request):
    student = _get_student_or_redirect(request)
    if not student:
        return redirect('lms:dashboard')
    homeworks = Homework.objects.filter(group=student.group).select_related('group', 'teacher') \
        .prefetch_related('submissions')
    submissions = {s.homework_id: s for s in student.submissions.all()}
    return render(request, 'lms/student/homework.html', {
        'student': student,
        'frozen': student.is_frozen(),
        'homeworks': homeworks,
        'submissions': submissions,
        'active_section': 'homework',
        'page_title': 'Домашние задания — Edu Point',
    })


@login_required
@role_required('student')
def student_homework_submit(request, pk):
    student = _get_student_or_redirect(request)
    if not student:
        return redirect('lms:dashboard')
    if student.is_frozen():
        messages.error(request, 'Доступ ограничен из-за неоплаты.')
        return redirect('lms:student_homework')
    homework = get_object_or_404(Homework, pk=pk, group=student.group)
    existing = student.submissions.filter(homework=homework).first()

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = existing or form.save(commit=False)
            submission.homework = homework
            submission.student = student
            submission.text = form.cleaned_data['text']
            if form.cleaned_data.get('photo'):
                submission.photo = form.cleaned_data['photo']
            if homework.due_date and homework.due_date < timezone.localdate():
                submission.is_late = True
            submission.save()
            messages.success(request, 'Ответ отправлен!')
            return redirect('lms:student_homework')
        messages.error(request, 'Проверьте форму.')
    else:
        form = SubmissionForm(initial={'text': existing.text if existing else ''})

    return render(request, 'lms/student/homework_submit.html', {
        'student': student,
        'homework': homework,
        'existing': existing,
        'form': form,
        'active_section': 'homework',
        'page_title': f'Ответ: {homework.title} — Edu Point',
    })


@login_required
@role_required('student')
def student_schedule(request):
    student = _get_student_or_redirect(request)
    if not student:
        return redirect('lms:dashboard')
    group = student.group
    days = []
    if group:
        codes = [d.strip() for d in group.days.split(',') if d.strip()]
        for code in DAY_ORDER:
            days.append({'code': code, 'label': DAY_LABELS[code],
                         'active': code in codes, 'group': group})
    return render(request, 'lms/student/schedule.html', {
        'student': student,
        'group': group,
        'days': days,
        'active_section': 'schedule',
        'page_title': 'Расписание — Edu Point',
    })


@login_required
@role_required('student')
def student_announcements(request):
    student = _get_student_or_redirect(request)
    if not student:
        return redirect('lms:dashboard')
    qs = Announcement.objects.filter(is_active=True)
    if student.group:
        qs = qs.filter(Q(group=student.group) | Q(group__isnull=True))
    else:
        qs = qs.filter(group__isnull=True)
    return render(request, 'lms/student/announcements.html', {
        'student': student,
        'announcements': qs.select_related('group', 'author').order_by('-created_at'),
        'active_section': 'announcements',
        'page_title': 'Объявления — Edu Point',
    })


# ---------------------------------------------------------------------------
# Кабинет родителя
# ---------------------------------------------------------------------------
@login_required
@role_required('parent')
def parent_dashboard(request):
    try:
        parent = request.user.parent_profile
    except ParentProfile.DoesNotExist:
        messages.error(request, 'Профиль родителя не найден.')
        return redirect('lms:dashboard')

    child_id = request.GET.get('child')
    children = parent.children.select_related('group', 'book', 'group__teacher')
    selected = None
    if child_id:
        selected = children.filter(pk=child_id).first()
    if not selected and children:
        selected = children.first()

    data = None
    if selected:
        data = {
            'grades': selected.grades.order_by('-date', '-created_at')[:30],
            'average': selected.average_grade(),
            'attendance': selected.attendance_stats(),
            'attendance_records': selected.attendance_records.order_by('-date')[:30],
            'payments': selected.payments.order_by('-month'),
            'frozen': selected.is_frozen(),
            'pay_status': selected.payment_status(),
            'debt': selected.debt_amount(),
            'homeworks': Homework.objects.filter(group=selected.group).select_related('group', 'teacher'),
            'submissions': {s.homework_id: s for s in selected.submissions.all()},
            'comments': [g for g in selected.grades.filter(comment__gt='').order_by('-date')[:20]],
        }

    return render(request, 'lms/parent/dashboard.html', {
        'parent': parent,
        'children': children,
        'selected': selected,
        'data': data,
        'active_section': 'overview',
        'page_title': 'Родительский кабинет — Edu Point',
    })


# ---------------------------------------------------------------------------
# Кабинет учителя
# ---------------------------------------------------------------------------
def _get_teacher_or_redirect(request):
    try:
        tp = request.user.teacher_profile
        if tp.teacher is None:
            messages.error(request, 'К вашему аккаунту не привязана карточка преподавателя.')
            return None
        return tp
    except TeacherProfile.DoesNotExist:
        messages.error(request, 'Профиль учителя не найден.')
        return None


@login_required
@role_required('teacher')
def teacher_dashboard(request):
    tp = _get_teacher_or_redirect(request)
    if not tp:
        return redirect('lms:dashboard')
    groups = Group.objects.filter(teacher=tp.teacher).annotate(
        student_count=Count('students')
    )
    today = timezone.localdate()
    return render(request, 'lms/teacher/dashboard.html', {
        'tp': tp,
        'groups': groups,
        'today': today,
        'active_section': 'overview',
        'page_title': 'Кабинет учителя — Edu Point',
    })


@login_required
@role_required('teacher')
def teacher_journal(request, group_pk):
    tp = _get_teacher_or_redirect(request)
    if not tp:
        return redirect('lms:dashboard')
    group = get_object_or_404(Group, pk=group_pk, teacher=tp.teacher)
    students = group.students.filter(is_active=True).select_related('user')

    date_str = request.GET.get('date', '')
    date = None
    if date_str:
        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            date = None
    if date is None:
        date = timezone.localdate()

    if request.method == 'POST':
        form = GradeAttendanceForm(request.POST, students=list(students), date=date)
        if form.is_valid():
            g_count, a_count = form.save(tp.teacher, group)
            log_request_activity(request, 'Обновил журнал',
                                 target=f'{group.name} ({date})',
                                 details=f'оценок: {g_count}, отметок: {a_count}')
            messages.success(request, f'Журнал сохранён: оценок — {g_count}, отметок — {a_count}.')
            return redirect(reverse('lms:teacher_journal', args=[group.pk]) + f'?date={date}')
        messages.error(request, 'Проверьте введённые данные.')
    else:
        form = GradeAttendanceForm(students=list(students), date=date)

    return render(request, 'lms/teacher/journal.html', {
        'tp': tp,
        'group': group,
        'students': students,
        'date': date,
        'form': form,
        'active_section': 'groups',
        'page_title': f'Журнал — {group.name} — Edu Point',
    })


@login_required
@role_required('teacher')
def teacher_homework(request):
    tp = _get_teacher_or_redirect(request)
    if not tp:
        return redirect('lms:dashboard')
    groups = Group.objects.filter(teacher=tp.teacher)
    homeworks = Homework.objects.filter(group__teacher=tp.teacher).select_related('group')

    if request.method == 'POST':
        form = HomeworkForm(request.POST, request.FILES)
        if form.is_valid():
            hw = form.save(commit=False)
            hw.teacher = tp.teacher
            hw.save()
            log_request_activity(request, 'Опубликовал задание', target=hw.title,
                                 details=f'группа: {hw.group.name}')
            for student in hw.group.students.filter(is_active=True):
                notify_student(student, f'Новое домашнее задание: «{hw.title}»',
                               reverse('lms:student_homework'))
            messages.success(request, 'Домашнее задание опубликовано.')
            return redirect('lms:teacher_homework')
        messages.error(request, 'Проверьте форму.')
    else:
        form = HomeworkForm()
        form.fields['group'].queryset = groups

    form.fields['group'].queryset = groups
    return render(request, 'lms/teacher/homework.html', {
        'tp': tp,
        'groups': groups,
        'homeworks': homeworks,
        'form': form,
        'active_section': 'homework',
        'page_title': 'Домашние задания — Edu Point',
    })


@login_required
@role_required('teacher')
def teacher_announcements(request):
    tp = _get_teacher_or_redirect(request)
    if not tp:
        return redirect('lms:dashboard')
    groups = Group.objects.filter(teacher=tp.teacher)
    announcements = Announcement.objects.filter(author=request.user).select_related('group')

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.author = request.user
            ann.save()
            log_request_activity(request, 'Опубликовал объявление', target=ann.title,
                                 details=f'группа: {ann.group.name if ann.group else "всем"}')
            if ann.group:
                for student in ann.group.students.filter(is_active=True):
                    notify_student(student, f'Объявление: «{ann.title}»',
                                   reverse('lms:student_announcements'))
            else:
                for student in StudentProfile.objects.filter(is_active=True):
                    notify_student(student, f'Объявление: «{ann.title}»',
                                   reverse('lms:student_announcements'))
            messages.success(request, 'Объявление опубликовано.')
            return redirect('lms:teacher_announcements')
        messages.error(request, 'Проверьте форму.')
    else:
        form = AnnouncementForm()

    form.fields['group'].queryset = groups
    return render(request, 'lms/teacher/announcements.html', {
        'tp': tp,
        'announcements': announcements,
        'form': form,
        'active_section': 'announcements',
        'page_title': 'Объявления — Edu Point',
    })


# ---------------------------------------------------------------------------
# Кабинет ресепшена
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def reception_dashboard(request):
    students = StudentProfile.objects.select_related('user', 'group', 'book')
    total = students.count()
    active = students.filter(is_active=True).count()
    frozen_ids = bulk_frozen_student_ids(students)
    frozen = [s for s in students if s.id in frozen_ids]
    overdue = len(frozen)
    today = timezone.localdate()
    recent_payments = Payment.objects.order_by('-paid_at').select_related('student__user')[:10]
    return render(request, 'lms/reception/dashboard.html', {
        'total': total,
        'active': active,
        'overdue': overdue,
        'frozen_count': len(frozen),
        'recent_payments': recent_payments,
        'today': today,
        'frozen_students': frozen[:8],
        'active_section': 'overview',
        'page_title': 'Кабинет ресепшена — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def reception_groups(request):
    groups = Group.objects.select_related('course', 'teacher', 'book', 'branch').annotate(
        s_count=Count('students')
    ).order_by('course__category__order', 'course__name', 'name')
    q = request.GET.get('q', '').strip()
    if q:
        groups = groups.filter(Q(name__icontains=q) | Q(teacher__name__icontains=q))
    return render(request, 'lms/reception/groups.html', {
        'groups': groups,
        'q': q,
        'active_section': 'groups',
        'page_title': 'Группы — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def reception_group_detail(request, pk):
    group = get_object_or_404(
        Group.objects.select_related('course', 'teacher', 'book', 'branch'), pk=pk
    )
    students = list(group.students.select_related('user', 'parent').order_by('user__last_name', 'user__first_name'))
    status_map = bulk_payment_status(students)
    for s in students:
        s.payment_status_cached = status_map.get(s.id, ('frozen', timezone.localdate().replace(day=1)))
    return render(request, 'lms/reception/group_detail.html', {
        'group': group,
        'students': students,
        'active_section': 'groups',
        'page_title': f'{group.name} — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def reception_teacher_add(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            teacher = form.save(commit=False)
            teacher.order = Teacher.objects.count()
            teacher.save()

            password = form.cleaned_data.get('password') or _generate_password()
            username = _generate_username(teacher.name, '', '')
            user = User.objects.create_user(username=username, password=password, first_name=teacher.name)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.role = 'teacher'
            profile.save(update_fields=['role'])
            TeacherProfile.objects.get_or_create(user=user, defaults={'teacher': teacher})
            teacher.user = user
            teacher.save(update_fields=['user'])

            log_request_activity(request, 'Добавил преподавателя', target=teacher.name,
                                 details=f'логин: {username}')
            messages.success(
                request,
                f'Преподаватель «{teacher.name}» добавлен. Логин для входа в кабинет: {username}, пароль: {password}'
            )
            return redirect('lms:reception_groups')
        messages.error(request, 'Проверьте форму.')
    else:
        form = TeacherForm()
    return render(request, 'lms/reception/teacher_add.html', {
        'form': form,
        'active_section': 'groups',
        'page_title': 'Новый преподаватель — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def reception_students(request):
    students = StudentProfile.objects.select_related('user', 'group', 'book', 'parent').annotate(
        group_student_count=Count('group__students')
    )
    q = request.GET.get('q', '').strip()
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) |
            Q(user__username__icontains=q) | Q(phone__icontains=q)
        )
    students = list(students.order_by('user__first_name'))
    status_map = bulk_payment_status(students)
    for s in students:
        s.payment_status_cached = status_map.get(s.id, ('frozen', timezone.localdate().replace(day=1)))

    counts = {
        'all': len(students),
        'frozen': sum(1 for s in students if s.payment_status_cached[0] == 'frozen'),
        'pending': sum(1 for s in students if s.payment_status_cached[0] == 'pending'),
        'paid': sum(1 for s in students if s.payment_status_cached[0] == 'paid'),
    }
    status_filter = request.GET.get('status', '')
    if status_filter in ('frozen', 'pending', 'paid'):
        students = [s for s in students if s.payment_status_cached[0] == status_filter]

    return render(request, 'lms/reception/students.html', {
        'students': students,
        'q': q,
        'counts': counts,
        'status_filter': status_filter,
        'active_section': 'students',
        'page_title': 'Ученики — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def reception_student_add(request):
    application_id = request.GET.get('application') or request.POST.get('application') or ''
    application = None
    if application_id:
        try:
            from applications.models import StudentApplication
            application = StudentApplication.objects.select_related('group_set').filter(pk=application_id).first()
        except Exception:
            application = None

    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            group = form.cleaned_data.get('group')
            if group and group.is_full():
                messages.error(request, f'Группа «{group.name}» заполнена (лимит {group.capacity}). '
                                        'Выберите другую группу или увеличьте лимит.')
                return render(request, 'lms/reception/student_add.html', {
                    'form': form,
                    'application': application,
                    'active_section': 'students',
                    'page_title': 'Новый ученик — Edu Point',
                })
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone = form.cleaned_data.get('phone', '')
            password = form.cleaned_data.get('password') or _generate_password()
            username = _generate_username(first_name, last_name, phone)

            user = User.objects.create_user(
                username=username, password=password,
                first_name=first_name, last_name=last_name,
            )
            profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'student', 'phone': phone})
            profile.role = 'student'
            profile.phone = phone
            profile.save()

            student = form.save(commit=False)
            student.user = user
            student.save()

            # Привязка к заявке (если пришли из CRM)
            if application:
                from applications.services import set_application_status
                application.student = student
                application.updated_by = request.user
                application.save(update_fields=['student', 'updated_by'])
                set_application_status(application, 'enrolled', user=request.user, note='Ученик создан')

            log_request_activity(request, 'Создал ученика', target=f'{first_name} {last_name}',
                                 details=f'логин: {username}, группа: {student.group.name if student.group else "—"}')
            messages.success(request, f'Ученик создан. Логин: {username}, пароль: {password}')
            return redirect('lms:reception_student_detail', pk=student.pk)
        messages.error(request, 'Проверьте форму.')
    else:
        form = StudentForm()
        if application:
            form.initial['first_name'] = application.name
            form.initial['phone'] = application.phone
            if application.group_set and application.group_set.group_id:
                form.initial['group'] = application.group_set.group_id
    return render(request, 'lms/reception/student_add.html', {
        'form': form,
        'application': application,
        'active_section': 'students',
        'page_title': 'Новый ученик — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def reception_student_detail(request, pk):
    student = get_object_or_404(StudentProfile.objects.select_related('user', 'group', 'book', 'parent'), pk=pk)
    pay_status = student.payment_status()

    payment_form = PaymentForm()
    extension_form = ExtensionForm()

    if request.method == 'POST':
        if request.POST.get('form') == 'payment':
            payment_form = PaymentForm(request.POST)
            if payment_form.is_valid():
                pay = payment_form.save(commit=False)
                pay.student = student
                pay.created_by = request.user
                pay.save()
                log_request_activity(request, 'Зарегистрировал оплату',
                                     target=f'{student} — {pay.month.strftime("%m.%Y")}',
                                     details=f'{pay.amount} сом, метод: {pay.get_method_display()}')
                if pay.is_confirmed:
                    notify_student(student, 'Оплата подтверждена, доступ восстановлен.',
                                   reverse('lms:student_dashboard'))
                messages.success(request, f'Оплата {pay.month.strftime("%m.%Y")} зарегистрирована.')
                return redirect('lms:reception_student_detail', pk=student.pk)
        elif request.POST.get('form') == 'extension':
            extension_form = ExtensionForm(request.POST)
            if extension_form.is_valid():
                ext = extension_form.save(commit=False)
                ext.student = student
                ext.created_by = request.user
                ext.save()
                log_request_activity(request, 'Оформил отсрочку',
                                     target=f'{student}',
                                     details=f'до {ext.new_due_date}, причина: {ext.reason or "—"}')
                notify_student(student, f'Срок оплаты перенесён до {ext.new_due_date}.',
                               reverse('lms:student_dashboard'))
                messages.success(request, f'Отсрочка до {ext.new_due_date} добавлена.')
                return redirect('lms:reception_student_detail', pk=student.pk)
        messages.error(request, 'Проверьте форму.')

    return render(request, 'lms/reception/student_detail.html', {
        'student': student,
        'pay_status': pay_status,
        'payments': student.payments.order_by('-month'),
        'extensions': student.extensions.order_by('-month'),
        'payment_form': payment_form,
        'extension_form': extension_form,
        'active_section': 'students',
        'page_title': f'Ученик: {student} — Edu Point',
    })


# ---------------------------------------------------------------------------
# Уведомления, журнал действий, аналитика
# ---------------------------------------------------------------------------
@login_required
def notifications_view(request):
    """Список уведомлений пользователя; при просмотре помечаются прочитанными."""
    notifications = request.user.lms_notifications.select_related('user')
    unread = notifications.filter(is_read=False).update(is_read=True)
    if unread:
        messages.info(request, f'Отмечено прочитанными: {unread}.')
    return render(request, 'lms/notifications.html', {
        'notifications': notifications[:100],
        'active_section': 'notifications',
        'page_title': 'Уведомления — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def activity_log_view(request):
    """История действий сотрудников."""
    logs = ActivityLog.objects.select_related('user').order_by('-created_at')
    q = request.GET.get('q', '').strip()
    if q:
        logs = logs.filter(Q(action__icontains=q) | Q(target__icontains=q) | Q(details__icontains=q))
    return render(request, 'lms/activity_log.html', {
        'logs': logs[:200],
        'q': q,
        'active_section': 'activity',
        'page_title': 'История действий — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def admin_analytics(request):
    """Аналитика для администратора/ресепшена."""
    students = StudentProfile.objects.all()
    today = timezone.localdate()
    month_start = today.replace(day=1)

    revenue_total = Payment.objects.filter(is_confirmed=True).aggregate(t=models_sum('amount'))['t'] or 0
    revenue_month = Payment.objects.filter(is_confirmed=True, month__year=today.year,
                                           month__month=today.month).aggregate(t=models_sum('amount'))['t'] or 0
    payments_month_count = Payment.objects.filter(is_confirmed=True, month__year=today.year,
                                                  month__month=today.month).count()

    frozen_ids = bulk_frozen_student_ids(students)
    frozen = [s for s in students if s.id in frozen_ids]

    groups_stats = Group.objects.annotate(s_count=Count('students'), avg_grade=Avg('grades__value'))
    overall_avg = Grade.objects.aggregate(a=Avg('value'))['a']
    overall_att = Attendance.objects.aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        late=Count('id', filter=Q(status='late')),
    )

    top_books = Book.objects.annotate(
        s_count=Count('students')
    ).filter(is_active=True).order_by('-s_count')[:5]

    by_status = {
        'active': students.filter(is_active=True).count(),
        'frozen': len(frozen),
    }

    context = {
        'total_students': students.count(),
        'active_students': by_status['active'],
        'frozen_count': by_status['frozen'],
        'revenue_total': revenue_total,
        'revenue_month': revenue_month,
        'payments_month_count': payments_month_count,
        'groups_stats': groups_stats,
        'overall_avg': round(overall_avg, 1) if overall_avg is not None else None,
        'attendance': overall_att,
        'top_books': top_books,
        'recent_activity': ActivityLog.objects.select_related('user').order_by('-created_at')[:15],
        'today': today,
        'active_section': 'analytics',
        'page_title': 'Аналитика — Edu Point',
    }
    return render(request, 'lms/admin_analytics.html', context)


# ---------------------------------------------------------------------------
# Объявления (общие)
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def reception_announcements(request):
    announcements = Announcement.objects.select_related('group', 'author')
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            ann = form.save(commit=False)
            ann.author = request.user
            ann.save()
            log_request_activity(request, 'Опубликовал объявление', target=ann.title,
                                 details=f'группа: {ann.group.name if ann.group else "всем"}')
            if ann.group:
                for student in ann.group.students.filter(is_active=True):
                    notify_student(student, f'Объявление: «{ann.title}»',
                                   reverse('lms:student_announcements'))
            else:
                for student in StudentProfile.objects.filter(is_active=True):
                    notify_student(student, f'Объявление: «{ann.title}»',
                                   reverse('lms:student_announcements'))
            messages.success(request, 'Объявление опубликовано.')
            return redirect('lms:reception_announcements')
        messages.error(request, 'Проверьте форму.')
    else:
        form = AnnouncementForm()
    return render(request, 'lms/reception/announcements.html', {
        'announcements': announcements,
        'form': form,
        'active_section': 'announcements',
        'page_title': 'Объявления — Edu Point',
    })
