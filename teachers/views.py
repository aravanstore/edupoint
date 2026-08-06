from django.shortcuts import render
from .models import Teacher


def teacher_list(request):
    """Страница преподавателей."""
    teachers = Teacher.objects.filter(is_active=True)
    context = {
        'teachers': teachers,
        'page_title': 'Наши преподаватели — Edu Point',
        'meta_description': 'Опытные преподаватели Edu Point. Корейский, английский, немецкий и китайский языки.',
    }
    return render(request, 'teachers/list.html', context)
