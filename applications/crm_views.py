"""CRM-представления: управление наборами, воронка заявок, лист ожидания."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from lms.models import Group
from lms.views import role_required
from lms.utils import log_request_activity
from core.telegram_utils import notify_new_application, send_telegram_message

from .forms import GroupSetForm, WaitlistForm, ApplicationNoteForm, ApplicationStatusForm
from .models import GroupSet, StudentApplication, WaitlistEntry
from .services import check_group_set_fill, notify_staff, set_application_status

# Этапы воронки (по порядку) — для конверсии
FUNNEL_STAGES = ['new', 'contacted', 'test', 'test_passed', 'enrolled']


# ---------------------------------------------------------------------------
# Наборы групп
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def set_list(request):
    status_filter = request.GET.get('status', '')
    qs = GroupSet.objects.select_related('course', 'teacher', 'branch')
    if status_filter:
        qs = qs.filter(status=status_filter)
    counts = {
        'open': GroupSet.objects.filter(status='open').count(),
        'closed': GroupSet.objects.filter(status='closed').count(),
        'archived': GroupSet.objects.filter(status='archived').count(),
    }
    sets = list(qs)
    for s in sets:
        s.app_count = s.reserved_count()
        s.seats_left_val = s.seats_left()
        s.fill = s.fill_percent()
    return render(request, 'applications/crm/set_list.html', {
        'sets': sets,
        'status_filter': status_filter,
        'counts': counts,
        'active_section': 'sets',
        'page_title': 'Наборы групп — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def set_create(request):
    form = GroupSetForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        group_set = form.save(commit=False)
        group_set.created_by = request.user
        group_set.save()
        log_request_activity(request, 'Создал набор', target=group_set.name,
                             details=f'курс: {group_set.course.name}')
        notify_staff(f'Открыт новый набор «{group_set.name}» — {group_set.course.name}',
                     reverse('applications:set_detail', kwargs={'pk': group_set.pk}))
        messages.success(request, f'Набор «{group_set.name}» создан.')
        return redirect('applications:set_detail', pk=group_set.pk)
    return render(request, 'applications/crm/set_form.html', {
        'form': form,
        'mode': 'create',
        'active_section': 'sets',
        'page_title': 'Новый набор — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def set_edit(request, pk):
    group_set = get_object_or_404(GroupSet, pk=pk)
    form = GroupSetForm(request.POST or None, instance=group_set)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_request_activity(request, 'Изменил набор', target=group_set.name)
        messages.success(request, 'Набор обновлён.')
        return redirect('applications:set_detail', pk=group_set.pk)
    return render(request, 'applications/crm/set_form.html', {
        'form': form,
        'group_set': group_set,
        'mode': 'edit',
        'active_section': 'sets',
        'page_title': f'Набор: {group_set.name} — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def set_detail(request, pk):
    group_set = get_object_or_404(
        GroupSet.objects.select_related('course', 'teacher', 'branch', 'group'), pk=pk)
    applications = group_set.applications.select_related('created_by').order_by('-created_at')
    waitlist = group_set.waitlist.all()
    status_form = ApplicationStatusForm()
    waitlist_form = WaitlistForm()
    return render(request, 'applications/crm/set_detail.html', {
        'group_set': group_set,
        'applications': applications,
        'waitlist': waitlist,
        'status_form': status_form,
        'waitlist_form': waitlist_form,
        'app_count': group_set.reserved_count(),
        'seats_left': group_set.seats_left(),
        'fill': group_set.fill_percent(),
        'active_section': 'sets',
        'page_title': f'Набор: {group_set.name} — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
@require_POST
def set_status(request, pk):
    group_set = get_object_or_404(GroupSet, pk=pk)
    action = request.POST.get('action')
    if action in ('open', 'close', 'archive'):
        mapping = {'open': 'open', 'close': 'closed', 'archive': 'archived'}
        group_set.status = mapping[action]
        group_set.save(update_fields=['status'])
        labels = {'open': 'открыт', 'close': 'закрыт', 'archive': 'архивирован'}
        log_request_activity(request, f'Набор {labels[action]}', target=group_set.name)
        messages.success(request, f'Набор «{group_set.name}» {labels[action]}.')
    return redirect('applications:set_detail', pk=group_set.pk)


@login_required
@role_required('reception', 'admin')
@require_POST
def set_create_group(request, pk):
    group_set = get_object_or_404(GroupSet, pk=pk)
    if group_set.group_id:
        messages.warning(request, 'Для этого набора уже создана группа.')
        return redirect('applications:set_detail', pk=group_set.pk)
    group = Group.objects.create(
        name=group_set.name,
        course=group_set.course,
        teacher=group_set.teacher,
        days=group_set.days,
        start_time=group_set.start_time,
        end_time=group_set.end_time,
        capacity=group_set.capacity,
        status='active',
        started_at=group_set.start_date or timezone.localdate(),
        branch=group_set.branch,
    )
    group_set.group = group
    group_set.save(update_fields=['group'])
    log_request_activity(request, 'Создал группу из набора', target=group.name,
                         details=f'набор: {group_set.name}')
    messages.success(request, f'Группа «{group.name}» создана. Зачисляйте учеников через раздел «Ученики».')
    return redirect('applications:set_detail', pk=group_set.pk)


# ---------------------------------------------------------------------------
# Воронка заявок
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def application_list(request):
    qs = StudentApplication.objects.select_related('course', 'group_set').order_by('-created_at')

    status_filter = request.GET.get('status', '')
    source_filter = request.GET.get('source', '')
    set_filter = request.GET.get('set', '')
    q = request.GET.get('q', '').strip()

    if status_filter:
        qs = qs.filter(status=status_filter)
    if source_filter:
        qs = qs.filter(source=source_filter)
    if set_filter:
        qs = qs.filter(group_set_id=set_filter)
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(phone__icontains=q))

    # Сводка по статусам (текущим)
    by_status = dict(qs.values_list('status').annotate(c=Count('id')).values_list('status', 'c'))

    # Сколько заявок когда-либо достигали каждого этапа (точная конверсия)
    reached = {}
    for stage in FUNNEL_STAGES:
        reached[stage] = StudentApplication.objects.filter(
            Q(status=stage) | Q(status_history__new_status=stage)
        ).distinct().count()

    funnel = []
    for i, stage in enumerate(FUNNEL_STAGES):
        prev = reached[FUNNEL_STAGES[i - 1]] if i > 0 else reached[stage]
        conv = round(reached[stage] / prev * 100) if prev else 0
        funnel.append({
            'code': stage,
            'label': StudentApplication.STATUS_DICT[stage],
            'count': reached[stage],
            'conv': conv if i > 0 else None,
        })

    return render(request, 'applications/crm/application_list.html', {
        'applications': qs[:200],
        'by_status': by_status,
        'funnel': funnel,
        'statuses': StudentApplication.STATUS_CHOICES,
        'sources': StudentApplication.SOURCE_CHOICES,
        'sets': GroupSet.objects.order_by('-created_at')[:50],
        'status_filter': status_filter,
        'source_filter': source_filter,
        'set_filter': set_filter,
        'q': q,
        'active_section': 'applications',
        'page_title': 'Заявки (воронка) — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
def application_detail(request, pk):
    application = get_object_or_404(
        StudentApplication.objects.select_related('course', 'group_set', 'created_by'), pk=pk)
    status_form = ApplicationStatusForm(initial={'status': application.status})
    note_form = ApplicationNoteForm(instance=application)
    history = application.status_history.select_related('changed_by').order_by('created_at')
    return render(request, 'applications/crm/application_detail.html', {
        'application': application,
        'status_form': status_form,
        'note_form': note_form,
        'history': history,
        'active_section': 'applications',
        'page_title': f'Заявка: {application.name} — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
@require_POST
def application_status(request, pk):
    application = get_object_or_404(StudentApplication, pk=pk)
    form = ApplicationStatusForm(request.POST)
    if form.is_valid():
        note = form.cleaned_data.get('note', '')
        changed = set_application_status(
            application, form.cleaned_data['status'], user=request.user, note=note)
        if changed:
            notify_staff(f'Заявка {application.name} переведена в «{application.get_status_display()}»',
                         reverse('applications:application_detail', kwargs={'pk': application.pk}))
            messages.success(request, 'Статус заявки обновлён.')
        else:
            messages.info(request, 'Статус уже такой.')
    else:
        messages.error(request, 'Проверьте данные формы.')
    return redirect('applications:application_detail', pk=application.pk)


@login_required
@role_required('reception', 'admin')
@require_POST
def application_notes(request, pk):
    application = get_object_or_404(StudentApplication, pk=pk)
    form = ApplicationNoteForm(request.POST, instance=application)
    if form.is_valid():
        application.updated_by = request.user
        form.save()
        log_request_activity(request, 'Обновил заметки заявки', target=application.name)
        messages.success(request, 'Заметки сохранены.')
    return redirect('applications:application_detail', pk=application.pk)


@login_required
@role_required('reception', 'admin')
def application_create(request):
    """Ручное создание заявки ресепшеном (звонок/визит)."""
    sets = GroupSet.objects.filter(status='open').select_related('course', 'teacher')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        set_id = request.POST.get('group_set', '')
        source = request.POST.get('source', 'other')
        comment = request.POST.get('comment', '').strip()
        if not (name and phone):
            messages.error(request, 'Укажите имя и телефон.')
        elif set_id:
            group_set = get_object_or_404(GroupSet, pk=set_id)
            if group_set.status != 'open':
                messages.error(request, 'Набор закрыт.')
            elif group_set.is_full():
                messages.error(request, 'В наборе нет мест — добавьте в лист ожидания.')
            else:
                application = StudentApplication.objects.create(
                    name=name, phone=phone, course=group_set.course, group_set=group_set,
                    source=source, comment=comment, created_by=request.user,
                )
                set_application_status(application, 'new', user=request.user, note='Заявка от ресепшена')
                log_request_activity(request, 'Создал заявку вручную', target=application.name,
                                     details=f'набор: {group_set.name}')
                check_group_set_fill(group_set)
                messages.success(request, 'Заявка создана.')
                return redirect('applications:application_detail', pk=application.pk)
        else:
            messages.error(request, 'Выберите набор.')
    return render(request, 'applications/crm/application_create.html', {
        'sets': sets,
        'sources': StudentApplication.SOURCE_CHOICES,
        'levels': StudentApplication.LEVEL_CHOICES,
        'active_section': 'applications',
        'page_title': 'Новая заявка — Edu Point',
    })


# ---------------------------------------------------------------------------
# Лист ожидания
# ---------------------------------------------------------------------------
@login_required
@role_required('reception', 'admin')
def waitlist_list(request):
    qs = WaitlistEntry.objects.select_related('group_set').order_by('-created_at')
    set_filter = request.GET.get('set', '')
    if set_filter:
        qs = qs.filter(group_set_id=set_filter)
    return render(request, 'applications/crm/waitlist.html', {
        'entries': qs[:300],
        'sets': GroupSet.objects.order_by('-created_at')[:50],
        'set_filter': set_filter,
        'active_section': 'waitlist',
        'page_title': 'Лист ожидания — Edu Point',
    })


@login_required
@role_required('reception', 'admin')
@require_POST
def waitlist_add(request, set_pk):
    group_set = get_object_or_404(GroupSet, pk=set_pk)
    form = WaitlistForm(request.POST)
    if form.is_valid():
        form.instance.group_set = group_set
        form.save()
        log_request_activity(request, 'Добавил в лист ожидания', target=group_set.name,
                             details=f'{form.instance.name}')
        messages.success(request, 'Запись добавлена в лист ожидания.')
    else:
        messages.error(request, 'Заполните имя и телефон.')
    return redirect('applications:set_detail', pk=group_set.pk)


@login_required
@role_required('reception', 'admin')
@require_POST
def waitlist_mark_notified(request, pk):
    entry = get_object_or_404(WaitlistEntry, pk=pk)
    entry.notified = True
    entry.save(update_fields=['notified'])
    log_request_activity(request, 'Отметил уведомление листа ожидания', target=entry.name)
    send_telegram_message(
        f'📞 <b>ЛИСТ ОЖИДАНИЯ — появилось место!</b>\n'
        f'📦 {entry.group_set.name}\n👤 {entry.name}\n📞 {entry.phone}'
    )
    messages.success(request, f'Уведомление отправлено в Telegram для {entry.name}.')
    return redirect('applications:waitlist_list')
