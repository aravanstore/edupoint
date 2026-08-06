from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Review
from courses.models import Course
from core.telegram_utils import notify_new_review


def review_list(request):
    """Страница отзывов + обработка отправки отзыва."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        text = request.POST.get('text', '').strip()
        rating = request.POST.get('rating', '5')
        course_id = request.POST.get('course', '')
        photo = request.FILES.get('photo')

        if name and text:
            try:
                rating_val = int(rating)
            except ValueError:
                rating_val = 5

            course_obj = None
            if course_id and course_id.isdigit():
                course_obj = Course.objects.filter(id=int(course_id)).first()

            review = Review.objects.create(
                name=name,
                text=text,
                rating=rating_val,
                course=course_obj,
                is_approved=False  # Модерация администратором
            )

            if photo:
                review.photo = photo
                review.save()

            # Отправка уведомления модератору в Telegram
            notify_new_review(review)

            messages.success(
                request,
                'Ваш отзыв успешно отправлен и будет опубликован после проверки модератором!'
            )
            return redirect('reviews:list')
        else:
            messages.error(request, 'Пожалуйста, заполните ваше имя и текст отзыва.')

    reviews = Review.objects.filter(is_approved=True)
    courses = Course.objects.all()

    context = {
        'reviews': reviews,
        'courses': courses,
        'page_title': 'Отзывы студентов — Edu Point',
        'meta_description': 'Отзывы наших студентов об учёбе в Edu Point.',
    }
    return render(request, 'reviews/list.html', context)
