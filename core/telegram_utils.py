"""
Утилита для отправки уведомлений в Telegram.
Используется при новых заявках с сайта.
"""
import requests
from django.conf import settings


def send_telegram_message(text: str) -> bool:
    """
    Отправляет сообщение в Telegram чат.
    Возвращает True при успехе, False при ошибке.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    if not token or not chat_id:
        return False

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
    }

    try:
        response = requests.post(url, data=payload, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False


def notify_new_application(application) -> bool:
    """
    Формирует и отправляет уведомление о новой заявке.
    """
    course_name = application.course.name if application.course else 'Не указан'

    text = (
        f"🎓 <b>НОВАЯ ЗАЯВКА — Edu Point</b>\n\n"
        f"👤 <b>Имя:</b> {application.name}\n"
        f"📞 <b>Телефон:</b> {application.phone}\n"
        f"🎂 <b>Возраст:</b> {application.age or 'Не указан'}\n"
        f"📚 <b>Курс:</b> {course_name}\n"
        f"📊 <b>Уровень:</b> {application.get_language_level_display()}\n"
        f"💬 <b>Комментарий:</b> {application.comment or 'Нет'}\n\n"
        f"⏰ Заявка получена. Свяжитесь с клиентом!"
    )
    return send_telegram_message(text)


def notify_new_contact(message) -> bool:
    """
    Уведомление о новом сообщении из формы обратной связи.
    """
    text = (
        f"✉️ <b>НОВОЕ СООБЩЕНИЕ — Edu Point</b>\n\n"
        f"👤 <b>Имя:</b> {message.name}\n"
        f"📞 <b>Телефон:</b> {message.phone or 'Не указан'}\n"
        f"📧 <b>Email:</b> {message.email or 'Не указан'}\n"
        f"💬 <b>Сообщение:</b>\n{message.message}"
    )
    return send_telegram_message(text)


def notify_new_review(review) -> bool:
    """
    Уведомление о новом отзыве, ожидающем модерации.
    """
    stars = '⭐' * (review.rating or 5)
    course_name = review.course.name if review.course else 'Общий отзыв'

    text = (
        f"⭐ <b>НОВЫЙ ОТЗЫВ НА МОДЕРАЦИЮ — Edu Point</b>\n\n"
        f"👤 <b>Автор:</b> {review.name}\n"
        f"🎓 <b>Курс:</b> {course_name}\n"
        f"📊 <b>Оценка:</b> {stars} ({review.rating}/5)\n\n"
        f"💬 <b>Текст отзыва:</b>\n<i>«{review.text}»</i>\n\n"
        f"⏰ Отзыв отправлен. Одобрите его в админ-панели для публикации на сайте!"
    )
    return send_telegram_message(text)
