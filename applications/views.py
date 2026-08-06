from django.shortcuts import render, redirect
from django.contrib import messages
from .models import StudentApplication
from courses.models import Course
from core.telegram_utils import notify_new_application


def apply(request):
    """Форма записи на курс."""
    courses = Course.objects.filter(is_active=True).select_related('category')
    selected_course_id = request.GET.get('course')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        age = request.POST.get('age', '')
        course_id = request.POST.get('course', '')
        language_level = request.POST.get('language_level', 'zero')
        comment = request.POST.get('comment', '').strip()

        if name and phone:
            course = None
            if course_id:
                try:
                    course = Course.objects.get(pk=course_id)
                except Course.DoesNotExist:
                    pass

            app = StudentApplication.objects.create(
                name=name,
                phone=phone,
                age=int(age) if age.isdigit() else None,
                course=course,
                language_level=language_level,
                comment=comment,
            )
            # Telegram уведомление
            notify_new_application(app)
            messages.success(request, '✅ Ваша заявка принята! Мы свяжемся с вами в ближайшее время.')
            return redirect('applications:apply')
        else:
            messages.error(request, 'Пожалуйста, заполните имя и телефон.')

    context = {
        'courses': courses,
        'selected_course_id': selected_course_id,
        'page_title': 'Записаться на курс — Edu Point',
        'meta_description': 'Оставьте заявку на курс в Edu Point. Мы свяжемся с вами и подберём удобное время.',
    }
    return render(request, 'applications/apply.html', context)
