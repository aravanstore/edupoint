from django.shortcuts import render, get_object_or_404
from .models import Course, Category


def course_list(request):
    """Каталог всех курсов."""
    categories = Category.objects.all()
    category_slug = request.GET.get('category', '')
    courses = Course.objects.filter(is_active=True).select_related('category', 'teacher')
    active_category = None

    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        courses = courses.filter(category=active_category)

    context = {
        'courses': courses,
        'categories': categories,
        'active_category': active_category,
        'page_title': 'Курсы — Edu Point',
        'meta_description': 'Курсы корейского, английского, немецкого и китайского языков. Подготовка к TOPIK, IELTS, GOETHE.',
    }
    return render(request, 'courses/list.html', context)


def course_detail(request, slug):
    """Детальная страница курса."""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    related_courses = Course.objects.filter(
        category=course.category, is_active=True
    ).exclude(pk=course.pk)[:3]

    context = {
        'course': course,
        'related_courses': related_courses,
        'schedules': course.schedules.all(),
        'reviews': course.reviews.filter(is_approved=True)[:5],
        'page_title': f'{course.name} — Edu Point',
        'meta_description': course.meta_description or course.short_description,
    }
    return render(request, 'courses/detail.html', context)


def language_page(request, slug):
    """Страница языкового направления (Korean, English, German, Chinese)."""
    category = get_object_or_404(Category, slug=slug)
    courses = Course.objects.filter(category=category, is_active=True).select_related('teacher')

    # Специальный шаблон для каждого языка
    template_map = {
        'korean': 'courses/korean.html',
        'english': 'courses/english.html',
        'german': 'courses/german.html',
        'chinese': 'courses/chinese.html',
    }
    template = template_map.get(category.language_code, 'courses/language.html')

    context = {
        'category': category,
        'courses': courses,
        'page_title': f'{category.name} язык — Edu Point',
        'meta_description': f'Курсы {category.name.lower()} языка в Edu Point. {category.description}',
    }
    return render(request, template, context)
