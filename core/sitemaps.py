from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from courses.models import Course
from news.models import NewsPost, BlogPost


class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'

    def items(self):
        return ['core:home', 'core:about', 'core:contact', 'core:gallery',
                'courses:list', 'exams:list', 'teachers:list',
                'reviews:list', 'applications:apply']

    def location(self, item):
        return reverse(item)


class CourseSitemap(Sitemap):
    priority = 0.8
    changefreq = 'monthly'

    def items(self):
        return Course.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.created_at


class NewsSitemap(Sitemap):
    priority = 0.7
    changefreq = 'daily'

    def items(self):
        return list(NewsPost.objects.filter(is_published=True)) + \
               list(BlogPost.objects.filter(is_published=True))

    def lastmod(self, obj):
        return obj.updated_at
