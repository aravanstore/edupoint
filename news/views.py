from django.shortcuts import render, get_object_or_404
from .models import NewsPost, BlogPost


def news_list(request):
    """Список новостей."""
    posts = NewsPost.objects.filter(is_published=True)
    context = {
        'posts': posts,
        'page_title': 'Новости — Edu Point',
        'meta_description': 'Последние новости учебного центра Edu Point.',
    }
    return render(request, 'news/list.html', context)


def news_detail(request, slug):
    """Детальная страница новости."""
    post = get_object_or_404(NewsPost, slug=slug, is_published=True)
    post.views += 1
    post.save(update_fields=['views'])
    related = NewsPost.objects.filter(is_published=True).exclude(pk=post.pk)[:3]
    context = {
        'post': post,
        'related': related,
        'page_title': f'{post.meta_title or post.title} — Edu Point',
        'meta_description': post.meta_description or post.excerpt,
    }
    return render(request, 'news/detail.html', context)


def blog_list(request):
    """Список статей блога."""
    category = request.GET.get('category', '')
    posts = BlogPost.objects.filter(is_published=True)
    if category:
        posts = posts.filter(category=category)
    context = {
        'posts': posts,
        'active_category': category,
        'categories': BlogPost.CATEGORY_CHOICES,
        'page_title': 'Блог — Edu Point',
        'meta_description': 'Советы по изучению языков, подготовке к экзаменам и учёбе за рубежом.',
    }
    return render(request, 'news/blog_list.html', context)


def blog_detail(request, slug):
    """Детальная страница статьи блога."""
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    post.views += 1
    post.save(update_fields=['views'])
    related = BlogPost.objects.filter(
        is_published=True, category=post.category
    ).exclude(pk=post.pk)[:3]
    context = {
        'post': post,
        'related': related,
        'page_title': f'{post.meta_title or post.title} — Edu Point',
        'meta_description': post.meta_description or post.excerpt,
    }
    return render(request, 'news/blog_detail.html', context)
