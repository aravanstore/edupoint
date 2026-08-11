from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from courses.models import Course
from core.telegram_utils import notify_new_application
from .models import GroupSet, StudentApplication, WaitlistEntry
from .services import check_group_set_fill, notify_staff, set_application_status


def apply(request):
    """Форма записи на курс: пользователь выбирает открытый набор."""
    open_sets = GroupSet.objects.filter(status='open').select_related('course', 'teacher', 'branch')
    visible_sets = [s for s in open_sets if s.can_apply()]
    selected_set_id = request.GET.get('set')
    course_filter = request.GET.get('course')
    course_filter_active = False
    if course_filter:
        filtered = [s for s in visible_sets
                    if s.course.slug == course_filter or s.course.category.slug == course_filter]
        if filtered:
            visible_sets = filtered
            course_filter_active = True

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        age = request.POST.get('age', '')
        set_id = request.POST.get('group_set', '')
        language_level = request.POST.get('language_level', 'zero')
        source = request.POST.get('source', 'other')
        comment = request.POST.get('comment', '').strip()

        if not (name and phone):
            messages.error(request, 'Пожалуйста, заполните имя и телефон.')
        elif not set_id:
            messages.error(request, 'Пожалуйста, выберите набор для записи.')
        else:
            group_set = get_object_or_404(GroupSet, pk=set_id)
            if group_set.status != 'open':
                messages.error(request, 'Этот набор закрыт. Выберите другой.')
            elif group_set.is_full():
                # Автоматически добавляем в лист ожидания
                WaitlistEntry.objects.create(
                    group_set=group_set, name=name, phone=phone, note=comment,
                )
                messages.info(request, 'Мест в этом наборе больше нет. Вы добавлены в лист ожидания — '
                                       'мы сообщим вам, когда появится место.')
                from core.telegram_utils import send_telegram_message
                send_telegram_message(
                    f'📋 <b>ЛИСТ ОЖИДАНИЯ — {group_set.name}</b>\n'
                    f'👤 {name}\n📞 {phone}\n💬 {comment or "—"}'
                )
            else:
                with transaction.atomic():
                    application = StudentApplication.objects.create(
                        name=name,
                        phone=phone,
                        age=int(age) if age.isdigit() else None,
                        course=group_set.course,
                        group_set=group_set,
                        source=source,
                        language_level=language_level,
                        comment=comment,
                    )
                    set_application_status(application, 'new', note='Заявка с сайта')
                notify_new_application(application)
                notify_staff(f'Новая заявка на набор «{group_set.name}»: {name}',
                             reverse('applications:application_detail', kwargs={'pk': application.pk}))
                check_group_set_fill(group_set)
                messages.success(request, '✅ Ваша заявка принята! Мы свяжемся с вами в ближайшее время.')
                return redirect('applications:apply')

    context = {
        'open_sets': visible_sets,
        'selected_set_id': selected_set_id,
        'course_filter': course_filter,
        'course_filter_active': course_filter_active,
        'page_title': 'Записаться на курс — Edu Point',
        'meta_description': 'Выберите открытый набор и оставьте заявку. Мы свяжемся с вами.',
    }
    return render(request, 'applications/apply.html', context)
