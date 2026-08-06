from django.shortcuts import render, get_object_or_404
from .models import Exam


def exam_list(request):
    """Страница экзаменов."""
    exams = Exam.objects.filter(is_active=True)
    context = {
        'exams': exams,
        'page_title': 'Подготовка к экзаменам TOPIK, IELTS, GOETHE — Edu Point',
        'meta_description': 'Подготовка к международным экзаменам TOPIK, IELTS и GOETHE в Edu Point.',
    }
    return render(request, 'exams/list.html', context)


def exam_detail(request, name):
    """Детальная страница экзамена."""
    exam = get_object_or_404(Exam, name=name, is_active=True)
    context = {
        'exam': exam,
        'page_title': f'Подготовка к {exam.get_name_display()} — Edu Point',
        'meta_description': exam.meta_description or f'Подготовка к экзамену {exam.get_name_display()} в Edu Point.',
    }
    return render(request, 'exams/detail.html', context)
