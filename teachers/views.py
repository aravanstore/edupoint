from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from .models import Teacher
from reviews.models import Review
from core.telegram_utils import notify_new_review


def teacher_list(request):
    """Страница преподавателей."""
    teachers = Teacher.objects.filter(is_active=True)
    context = {
        'teachers': teachers,
        'page_title': 'Наши преподаватели — Edu Point',
        'meta_description': 'Опытные преподаватели Edu Point. Корейский, английский, немецкий и китайский языки.',
    }
    return render(request, 'teachers/list.html', context)


def teacher_detail(request, pk):
    """Профиль преподавателя: инфо + отзывы + форма отзыва."""
    teacher = get_object_or_404(Teacher, pk=pk, is_active=True)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        text = request.POST.get('text', '').strip()
        rating = request.POST.get('rating', '5')
        photo = request.FILES.get('photo')

        if name and text:
            try:
                rating_val = int(rating)
            except ValueError:
                rating_val = 5
            rating_val = max(1, min(5, rating_val))

            review = Review.objects.create(
                name=name,
                text=text,
                rating=rating_val,
                teacher=teacher,
                is_approved=False,  # Модерация администратором
            )
            if photo:
                review.photo = photo
                review.save()

            notify_new_review(review)
            messages.success(
                request,
                'Спасибо! Ваш отзыв отправлен и будет опубликован после проверки модератором.'
            )
        else:
            messages.error(request, 'Пожалуйста, заполните имя и текст отзыва.')
        return redirect('teachers:detail', pk=teacher.pk)

    context = {
        'teacher': teacher,
        'reviews': teacher.approved_reviews(),
        'average_rating': teacher.average_rating(),
        'reviews_count': teacher.reviews_count(),
        'page_title': f'{teacher.name} — Edu Point',
        'meta_description': f'{teacher.name} — {teacher.position}. Отзывы студентов, опыт работы, языки преподавания.',
    }
    return render(request, 'teachers/detail.html', context)
