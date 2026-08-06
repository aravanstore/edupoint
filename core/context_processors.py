from .models import SiteSettings
from courses.models import Category


def site_settings(request):
    """Глобальный контекст: настройки сайта и категории языков доступны на всех страницах."""
    settings = SiteSettings.get()
    categories = Category.objects.all().order_by('order')
    return {
        'site_settings': settings,
        'language_categories': categories,
    }
