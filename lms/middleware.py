from django.utils.cache import add_never_cache_headers


class NoCacheAuthenticatedMiddleware:
    """Запрещает кеширование ответов для авторизованных пользователей.

    Защищает от попадания в личные кабинеты через кнопку «Назад» браузера
    после выхода из системы.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            add_never_cache_headers(response)
        return response
