# Edu Point — Веб-сайт Языкового Учебного Центра в Оше

Современный, динамичный, адаптивный веб-сайт учебного центра **Edu Point** (г. Ош, Кыргызстан) на **Django**.

![Edu Point](static/images/edu%20logo.jpg)

## 🌟 Основные особенности

- **Цветовая палитра**: Небесно-голубой (`#0EA5E9`) + тил/бирюзовый акцент (`#2A9D8F`) + белый.
- **18+ Полноценных страниц**: Главная, О нас, Каталог курсов, Корейский (с фокусом на TOPIK), Английский (IELTS), Немецкий (GOETHE), Китайский, Экзамены, Преподаватели, Новости, Блог, Галерея с фильтрами, Отзывы, Контакты (Google Maps), Запись на курс, Поиск.
- **Telegram Уведомления**: Автоматическая отправка новых заявок администратору в Telegram.
- **WhatsApp плавающая кнопка**: Прямая связь с учебным центром (+996 700 995 577).
- **Dark Mode**: Переключение светлой и тёмной темы с сохранением в `localStorage`.
- **Интерактивные функции**: Поиск (AJAX), лайтбокс галереи, анимация счетчиков, scroll animation.
- **CMS / Admin Panel**: Полное управление курсами, преподавателями, отзывами, новостями и галереей.
- **SEO Оптимизация**: Sitemap.xml, robots.txt, Open Graph meta tags, красивый Slug URLs.

---

## 🛠 Технологии

- **Backend**: Python 3.12, Django 4.2+, Django REST Framework (готовность к API)
- **Frontend**: HTML5, CSS3 (Vanilla CSS design system), JavaScript, Bootstrap 5.3, Bootstrap Icons
- **Database**: SQLite3 (готов к легкому переходу на PostgreSQL)
- **Integrations**: Telegram Bot API, Google Maps Embed

---

## 🚀 Быстрый запуск

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Примените миграции:
```bash
python manage.py migrate
```

3. Заполните базу демонстрационными данными:
```bash
python manage.py seed_data
```

4. Запустите сервер разработки:
```bash
python manage.py runserver
```

5. Откройте в браузере: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### 🔐 Админ-панель:
- **URL**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- **Логин**: `admin`
- **Пароль**: `admin12345`

---

## 📍 Контакты Edu Point

- **Адрес**: А. Масалиева 44, ТЦ Корона, 3 этаж, Osh, Kyrgyzstan
- **Телефон**: +996 700 995 577
- **Instagram**: [@edupoint.ec](https://www.instagram.com/edupoint.ec)
