"""
Django settings for Edu Point language learning center.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================================================================
# SECURITY
# ===========================================================================
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-edupoint-change-in-production-2026')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,edupoint.aravan.kg,.onrender.com,.koyeb.app').split(',')

# Production/HTTPS. По умолчанию выключено (dev + ngrok по http).
# Для продакшена задайте: SECURE_COOKIES=True, SECURE_SSL_REDIRECT=True
# (и при необходимости SECURE_HSTS_SECONDS=31536000).
SECURE_COOKIES = os.environ.get('SECURE_COOKIES', 'False') == 'True'
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES
SECURE_HSTS_SECONDS = int(os.environ.get('SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'SAMEORIGIN'
# Доверие к X-Forwarded-Proto от HTTPS-прокси (ngrok/nginx/render).
# Включайте только если за HTTPS-терминацией стоит прокси.
if os.environ.get('TRUST_PROXY_SSL', 'False') == 'True':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ngrok / external tunnel support
CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://*.ngrok-free.dev',
    'https://*.ngrok.io',
    'https://*.ngrok.dev',
    'https://*.koyeb.app',
    'https://*.onrender.com',
    'https://edupoint.aravan.kg',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# ===========================================================================
# APPLICATIONS
# ===========================================================================
INSTALLED_APPS = [
    # Django built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    # Third-party
    'rest_framework',
    'ckeditor',

    # Edu Point apps
    'core',
    'courses',
    'teachers',
    'applications',
    'reviews',
    'news',
    'exams',
    'games',

    # LMS — образовательная платформа
    'lms',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'lms.middleware.NoCacheAuthenticatedMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'edupoint.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'edupoint.wsgi.application'

# ===========================================================================
# DATABASE
# По умолчанию — SQLite (готово к работе из коробки).
# Для перехода на PostgreSQL задайте переменные окружения:
#   DB_ENGINE=django.db.backends.postgresql, DB_NAME, DB_USER, DB_PASSWORD,
#   DB_HOST, DB_PORT
# ===========================================================================
DB_ENGINE = os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3')
if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.environ.get('DB_NAME', 'edupoint'),
            'USER': os.environ.get('DB_USER', ''),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            # Держим соединение открытым между запросами вместо переоткрытия
            # каждый раз — база удалённая (Supabase, другой регион), поэтому
            # рукопожатие соединения ощутимо дорогое. 60с — умеренно, чтобы
            # не упереться в лимит соединений на бесплатном тарифе Supabase.
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
        }
    }

# ===========================================================================
# CACHE
# In-process (LocMemCache) — без внешних зависимостей вроде Redis. Годится
# для редко меняющихся данных (настройки сайта, категории и т.п.).
# ===========================================================================
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'edupoint-cache',
    }
}

# ===========================================================================
# AUTHENTICATION
# ===========================================================================
LOGIN_URL = 'lms:login'
LOGIN_REDIRECT_URL = 'lms:dashboard'
LOGOUT_REDIRECT_URL = 'lms:login'

# ===========================================================================
# PASSWORD VALIDATION
# ===========================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===========================================================================
# INTERNATIONALIZATION
# ===========================================================================
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Asia/Bishkek'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Публичный сайт: русский по умолчанию, автоопределение по браузеру
# (Accept-Language) + ручной переключатель в шапке. ЛМС (личный кабинет)
# не переводится — им пользуется только персонал в Оше.
LANGUAGES = [
    ('ru', 'Русский'),
    ('de', 'Deutsch'),
    ('ko', '한국어'),
    ('zh-hans', '中文'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# ===========================================================================
# STATIC & MEDIA FILES
# ===========================================================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Whitenoise: serve static files in production with compression + hashing
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# Whitenoise middleware is placed right after SecurityMiddleware above.

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ===========================================================================
# DEFAULT PRIMARY KEY
# ===========================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ===========================================================================
# TELEGRAM BOT
# ===========================================================================
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7569848532:AAGWG6p2LdKBVIN2oYJQHrBvyJq7uIAlRl8')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '-1003976333711')

# ===========================================================================
# EMAIL
# ===========================================================================
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@edupoint.kg')

# ===========================================================================
# DJANGO REST FRAMEWORK (prepared for future API)
# ===========================================================================
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}

# ===========================================================================
# CKEDITOR
# ===========================================================================
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source'],
        ],
    }
}

# ===========================================================================
# SITE CONFIGURATION
# ===========================================================================
SITE_NAME = 'Edu Point'
SITE_TAGLINE = 'Языковой центр в Оше'
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')
