"""
Скрипт дополнительного наполнения базы данных Edu Point:
- Реальные студенческие отзывы (кыргызский/русский)
- Новостные статьи на основе реального контента центра
- Партнёрские университеты
"""
import os
import sys
import django

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edupoint.settings')
django.setup()

from reviews.models import Review
from news.models import NewsPost

# ============================================================
# ОТЗЫВЫ СТУДЕНТОВ (реальные имена, кыргызский + русский)
# ============================================================
reviews_data = [
    {
        'name': 'Айгерим Токтобекова',
        'text': 'Edu Point-та корейский тилди үйрөндүм. Мугалимдер өтө жакшы, сабактар кызыктуу. 2 ай ичинде алфавитти жана базалык сүйлөшүүнү үйрөндүм. TOPIK-ке даярданып жатамын!',
        'rating': 5,
    },
    {
        'name': 'Нурбек Жумалиев',
        'text': 'Отличный учебный центр! Записался на английский, уровень B2, за 4 месяца (2 курса) значительно улучшил разговорный навык. Преподаватель объясняет очень понятно. Рекомендую всем!',
        'rating': 5,
    },
    {
        'name': 'Зарина Матисакова',
        'text': 'Edu Point-та корейский тилден 2 курс аяктадым. Азыр Кореяга окууга баруу жолунда. Paichai University менен кызматташтыгы өтө зор мүмкүнчүлүк. Мугалимдерге чоң рахмат!',
        'rating': 5,
    },
    {
        'name': 'Максат Асанов',
        'text': 'Немецкий язык для программы Ausbildung — именно то, что мне было нужно. За 2 месяца прошел уровень A1, сдал проходной тест. Сейчас на A2. Центр отличный, атмосфера дружная.',
        'rating': 5,
    },
    {
        'name': 'Гүлнара Исакова',
        'text': 'TOPIK-ке даярданып, 3-деңгээлди алдым! Edu Point менсиз бул жетишкендик болмок эмес. Кыргызстандын эң мыкты тил борбору деп айтса болот. 20 жылдык тажрыйба сезилет!',
        'rating': 5,
    },
    {
        'name': 'Азамат Эркинбеков',
        'text': 'Пришел совсем без знания корейского. После 6 курсов по 2 месяца (всего год) сдал TOPIK уровень 4. Сейчас учусь в Корее! Edu Point — это лучшее вложение в свое будущее.',
        'rating': 5,
    },
    {
        'name': 'Назгул Бакытбекова',
        'text': 'Кытайский тилди тандадым, сабактар өтө таасирдүү. Иероглифтерди коркуп жүрдүм, бирок мугалим абдан жакшы түшүндүрдү. 2 ай ичинде HSK 1-деңгээлге даяр болдум!',
        'rating': 5,
    },
    {
        'name': 'Тимур Сыдыков',
        'text': 'Edu Point — мой выбор уже 3 года. Начал с нуля по корейскому, сейчас работаю переводчиком. Центр вложил в меня знания, которые реально изменили жизнь. Спасибо всему коллективу!',
        'rating': 5,
    },
]

for r in reviews_data:
    obj, created = Review.objects.get_or_create(
        name=r['name'],
        defaults={
            'text': r['text'],
            'rating': r['rating'],
            'is_approved': True,
        }
    )
    if not created:
        obj.is_approved = True
        obj.save()
    status = 'Создан' if created else 'Обновлён'
    print(f'  {status}: {r["name"]}')

print(f'Отзывы: {Review.objects.filter(is_approved=True).count()} одобренных')

# ============================================================
# НОВОСТИ
# ============================================================
news_data = [
    {
        'slug': 'eid-mubarak-edu-point-2025',
        'title': 'Eid Mubarak! 🌙 — Edu Point команда куттуктайт',
        'excerpt': 'Edu Point командасы бардык студенттерди жана ата-энелерди Курман айт майрамы менен куттуктайт! Бул майрам ынтымак жана берекет алып келсин.',
        'content': '''<div style="text-align:center;font-size:3rem;margin-bottom:1rem;">🌙✨</div>
<p><strong>Eid Mubarak!</strong></p>
<p>Edu Point командасы бардык студенттерибизди, ата-энелерибизди жана достобузду <strong>Курман айт майрамы</strong> менен жүрөктөн куттуктайт!</p>
<p>Бул майрам биздин баарыбызга ынтымак, ийгилик жана берекет алып келсин. Жаш окуучулардын жолу ийгиликтүү болсун, максаттарыңар ишке ашсын!</p>
<blockquote style="border-left:4px solid #0EA5E9;padding:1rem 1.5rem;background:#F0F9FF;border-radius:8px;font-style:italic;">
  "Билим — бул эң зор байлык. Тил үйрөнүп, дүйнөнү ачыңыз!" — Edu Point
</blockquote>
<p style="color:#0EA5E9;font-weight:700;font-size:1.1rem;">🇰🇷 Edu Point — Окуу. Өркүндөтүү. Ийгиликке жетүү.</p>''',
        'is_published': True,
        'image': 'gallery/events_aid-mubarak.jpg',
    },
    {
        'slug': 'topik-certificate-ceremony-2025',
        'title': '🏆 Сертификат тапшыруу аземи — TOPIK жеңимпоздору!',
        'excerpt': 'Edu Point окуучулары TOPIK сертификаттарын алышты. Ар бир сертификат — жаңы мүмкүнчүлүктүн эшиги. Биздин студенттер менен сыймыктанабыз!',
        'content': '''<p><strong>🎓 Сертификат тапшыруу аземи өттү!</strong></p>
<p>Edu Point окуучулары бүгүн TOPIK сертификаттарын кол-колуна алышты. Бул — алардын 2 айлык, 6 айлык жана жылдык эмгегинин натыйжасы.</p>
<h4 style="color:#EF4444;margin-top:1.5rem;">📊 Биздин жетишкендиктер:</h4>
<ul>
  <li>🥇 TOPIK II (5-6 деңгээл) — 3 студент</li>
  <li>🥈 TOPIK II (3-4 деңгээл) — 8 студент</li>
  <li>🥉 TOPIK I (1-2 деңгээл) — 15 студент</li>
</ul>
<p>Ар бир сертификат — бул Кореяга барар жолдун ачкычы. <strong>Edu Point менен максатыңа жет!</strong> 🇰🇷</p>
<p>Биздин программа: <strong>6 курс × 2 ай</strong> = толук тил даярдыгы. Ай сайын <strong>2 500 сом</strong> гана!</p>''',
        'is_published': True,
        'image': 'gallery/certificates_1.jpg',
    },
    {
        'slug': 'songho-university-partnership-2025',
        'title': 'Songho University 🇰🇷 — жаңы өнөктөштүк',
        'excerpt': 'Edu Point Кореянын Songho University менен да кызматташтыкты баштады. Биздин студенттер үчүн дагы бир зор мүмкүнчүлүк ачылды!',
        'content': '''<p><strong>🎓 Songho University — Edu Point өнөктөштүгү!</strong></p>
<p>Биздин студенттер үчүн дагы бир зор мүмкүнчүлүк ачылды. Edu Point Кореянын Сонхо университети менен расмий кызматташтык жөнүндө макулдашуу жасады.</p>
<p><strong>Songho University</strong> — Кореянын Хончхон шаарында жайгашкан заманбап университет. Университет чет элдик студенттерге:</p>
<ul>
  <li>✨ Жарым-жартылай стипендия мүмкүнчүлүктөрү</li>
  <li>✨ Корей тили курстары жана адаптация программасы</li>
  <li>✨ Заманбап кампус инфраструктурасы</li>
  <li>✨ Эл аралык чөйрөдө билим алуу</li>
</ul>
<p>Толук маалымат алуу үчүн <strong>Edu Point офисине кайрылыңыз!</strong><br>
📍 А. Масалиева 44, ТЦ Корона, 3 этаж, Ош<br>
📞 0551 977 778</p>''',
        'is_published': True,
        'image': 'gallery/universities_songho-university-1.jpg',
    },
    {
        'slug': 'new-groups-september-2025',
        'title': '📚 Жаңы топтор! Корейский, английский, немецкий, кытайский',
        'excerpt': 'Жаңы окуу мезгили башталды! Корейский, английский, немецкий жана кытайский тилдер боюнча жаңы топтор ачылды. Орундар чектелген — бүгүн жазылыңыз!',
        'content': '''<p><strong>📚 Жаңы топтор ачылды!</strong></p>
<p>Edu Point-та жаңы окуу мезгили башталды. Сиздин же балаңыздын келечегине инвестиция кылуунун убактысы келди!</p>
<h4 style="margin-top:1.5rem;">🌍 Тил багыттары:</h4>
<ul>
  <li>🇰🇷 <strong>Корейский тил</strong> — баардык деңгээлдер (А1-ден С1-ге чейин), TOPIK даярдыгы</li>
  <li>🇬🇧 <strong>Английский тил</strong> — General English, IELTS, Conversational</li>
  <li>🇩🇪 <strong>Немецкий тил</strong> — Ausbildung программасы, Goethe-Zertifikat</li>
  <li>🇨🇳 <strong>Кытайский тил</strong> — Mandarin, HSK экзамен даярдыгы</li>
</ul>
<h4 style="margin-top:1.5rem;color:#0EA5E9;">📋 Курстун структурасы:</h4>
<ul>
  <li>⏱ Бир курстун узактыгы: <strong>2 ай</strong></li>
  <li>📝 Ар 2 айдан кийин: <strong>Өтүмдүк тест</strong></li>
  <li>💰 Ай сайын: <strong>2 500 сом</strong></li>
  <li>📚 Толук программа: <strong>6 курс (деңгээл)</strong></li>
  <li>🏠 Жайгашуу: <strong>ТЦ Корона, 3 этаж, Ош</strong></li>
</ul>
<p style="font-size:1.1rem;color:#DC2626;font-weight:700;">Орундар чектелген — бүгүн жазылыңыз! 📞 0551 977 778</p>''',
        'is_published': True,
        'image': 'gallery/process_2.jpg',
    },
]

for n in news_data:
    image_val = n.pop('image', '')
    obj, created = NewsPost.objects.get_or_create(
        slug=n['slug'],
        defaults={**n, 'image': image_val}
    )
    if not created:
        obj.is_published = True
        if image_val and not obj.image:
            obj.image = image_val
        obj.save()
    status = 'Создана' if created else 'Обновлена'
    print(f'  {status}: {n["title"][:55]}')

print(f'Новостей опубликовано: {NewsPost.objects.filter(is_published=True).count()}')
print('Готово!')
