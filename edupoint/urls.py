"""
Edu Point URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
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
