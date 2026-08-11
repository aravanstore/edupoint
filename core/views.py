from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Prefetch
from django.urls import reverse
from .models import GalleryImage, ContactMessage
from .telegram_utils import notify_new_contact
from courses.models import Course, Category
from teachers.models import Teacher
from reviews.models import Review
from news.models import NewsPost
from applications.models import GroupSet, StudentApplication
from exams.models import Exam


def home(request):
    """Главная страница."""
    featured_courses = Course.objects.filter(is_active=True, is_featured=True).select_related('category', 'teacher')[:6]
    categories = Category.objects.all()
    teachers = Teacher.objects.filter(is_active=True)[:4]
    reviews = Review.objects.filter(is_approved=True)[:6]
    latest_news = NewsPost.objects.filter(is_published=True)[:3]
    open_sets = list(
        GroupSet.objects.filter(status='open')
        .select_related('course', 'course__category', 'teacher')
        .prefetch_related(
            Prefetch(
                'applications',
                queryset=StudentApplication.objects.filter(
                    status__in=StudentApplication.ACTIVE_STATUSES
                ).order_by('created_at'),
                to_attr='active_applications',
            )
        )
        .order_by('-created_at')[:6]
    )

    stats = {
        'students': 500,
        'languages': 4,
        'exams': 3,
        'years': 5,
    }

    context = {
        'featured_courses': featured_courses,
        'categories': categories,
        'teachers': teachers,
        'reviews': reviews,
        'latest_news': latest_news,
        'open_sets': open_sets,
        'stats': stats,
        'page_title': 'Edu Point — Языковой центр в Оше',
        'meta_description': 'Изучайте корейский, английский, немецкий и китайский языки. Подготовка к TOPIK, IELTS, GOETHE. Ош, Кыргызстан.',
    }
    return render(request, 'core/home.html', context)


def about(request):
    """Страница «О нас»."""
    teachers = Teacher.objects.filter(is_active=True)
    context = {
        'teachers': teachers,
        'page_title': 'О нас — Edu Point',
        'meta_description': 'История, миссия и ценности учебного центра Edu Point. Узнайте, почему нас выбирают сотни студентов.',
    }
    return render(request, 'core/about.html', context)


def gallery(request):
    """Галерея фотографий."""
    category_filter = request.GET.get('category', '')
    images = GalleryImage.objects.all()
    if category_filter:
        images = images.filter(category=category_filter)

    context = {
        'images': images,
        'category_filter': category_filter,
        'page_title': 'Галерея — Edu Point',
        'meta_description': 'Фотографии классов, мероприятий и студентов учебного центра Edu Point.',
    }
    return render(request, 'core/gallery.html', context)


def contact(request):
    """Страница контактов с формой обратной связи."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        message_text = request.POST.get('message', '').strip()

        if name and message_text:
            msg = ContactMessage.objects.create(
                name=name, email=email, phone=phone, message=message_text
            )
            notify_new_contact(msg)
            messages.success(request, 'Ваше сообщение отправлено! Мы свяжемся с вами скоро.')
        else:
            messages.error(request, 'Пожалуйста, заполните имя и сообщение.')
        return redirect('core:contact')

    context = {
        'page_title': 'Контакты — Edu Point',
        'meta_description': 'Свяжитесь с нами. Адрес: А. Масалиева 44, ТЦ Корона, 3 этаж, Ош.',
    }
    return render(request, 'core/contact.html', context)


def search(request):
    """AJAX и обычный поиск по курсам, статьям, преподавателям и экзаменам."""
    query = request.GET.get('q', '').strip()
    results = {'courses': [], 'news': [], 'teachers': [], 'exams': []}

    if query:
        courses = Course.objects.filter(
            Q(name__icontains=query) | Q(short_description__icontains=query),
            is_active=True
        ).select_related('category')[:8]

        news = NewsPost.objects.filter(
            Q(title__icontains=query) | Q(excerpt__icontains=query),
            is_published=True
        )[:5]

        teachers = Teacher.objects.filter(
            Q(name__icontains=query) | Q(position__icontains=query) | Q(languages__icontains=query),
            is_active=True
        )[:6]

        exams = Exam.objects.filter(
            Q(name__icontains=query) | Q(full_name__icontains=query),
            is_active=True
        )[:4]

        results['courses'] = courses
        results['news'] = news
        results['teachers'] = teachers
        results['exams'] = exams

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'courses': [{'name': c.name, 'url': c.get_absolute_url(), 'category': c.category.name} for c in results['courses']],
            'news': [{'title': n.title, 'url': n.get_absolute_url()} for n in results['news']],
            'teachers': [{'name': t.name, 'url': reverse('teachers:detail', kwargs={'pk': t.pk}), 'position': t.position} for t in results['teachers']],
            'exams': [{'name': e.get_name_display(), 'url': reverse('exams:detail', kwargs={'name': e.name})} for e in results['exams']],
        }
        return JsonResponse(data)

    context = {
        'query': query,
        'courses': results['courses'],
        'news': results['news'],
        'teachers': results['teachers'],
        'exams': results['exams'],
        'page_title': f'Поиск: {query} — Edu Point',
    }
    return render(request, 'core/search.html', context)


def robots_txt(request):
    """robots.txt для поисковых систем."""
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/
Sitemap: {request.build_absolute_uri('/sitemap.xml')}
"""
    return HttpResponse(content, content_type='text/plain')
