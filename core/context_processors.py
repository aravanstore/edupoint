from django.core.cache import cache

from .models import SiteSettings
from courses.models import Category


def site_settings(request):
    """Глобальный контекст: настройки сайта и категории языков доступны на
    всех страницах — выполняется на КАЖДОМ запросе, поэтому кешируем
    (меняются редко, только через админку)."""
    settings = cache.get_or_set('site_settings', SiteSettings.get, 300)
    categories = cache.get_or_set(
        'language_categories', lambda: list(Category.objects.all().order_by('order')), 300
    )
    return {
        'site_settings': settings,
        'language_categories': categories,
    }
