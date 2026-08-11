"""
Edu Point URL Configuration
"""

import os

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as serve_media
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap, CourseSitemap, NewsSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'courses': CourseSitemap,
    'news': NewsSitemap,
}

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Переключатель языка (django.views.i18n.set_language)
    path('i18n/', include('django.conf.urls.i18n')),

    # Core pages
    path('', include('core.urls')),

    # Courses
    path('courses/', include('courses.urls')),

    # Exams
    path('exams/', include('exams.urls')),

    # Teachers
    path('teachers/', include('teachers.urls')),

    # News
    path('news/', include('news.urls', namespace='news')),

    # Blog
    path('blog/', include('news.blog_urls', namespace='blog')),

    # Reviews
    path('reviews/', include('reviews.urls')),

    # Games
    path('games/', include('games.urls', namespace='games')),

    # Applications
    path('apply/', include('applications.urls')),

    # LMS — личные кабинеты
    path('dashboard/', include('lms.urls')),

    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),

    # API (DRF — prepared for future)
    path('api/', include('core.api_urls')),
]

# Serve media and static files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Self-hosted production (Windows): serve uploaded media via Django
# (static is served by whitenoise). Enabled with SERVE_MEDIA=True.
if not settings.DEBUG and os.environ.get('SERVE_MEDIA', 'False') == 'True':
    urlpatterns += [
        path(f'{settings.MEDIA_URL.lstrip("/")}<path:path>',
             serve_media,
             {'document_root': settings.MEDIA_ROOT}),
    ]
