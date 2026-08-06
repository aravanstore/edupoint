from django.core.management.base import BaseCommand
from core.models import SiteSettings, GalleryImage
from courses.models import Category, Course
from teachers.models import Teacher
from reviews.models import Review
from news.models import NewsPost, BlogPost
from exams.models import Exam
import os


class Command(BaseCommand):
    help = 'Заполнение начальными данными (Seed Database with full Edu Point updates)'

    def handle(self, *args, **options):
        self.stdout.write('Обновление данных Edu Point...')

        # 1. Site Settings
        settings = SiteSettings.get()
        settings.phone = '0551977778 / +996 551 977 778'
        settings.whatsapp = '996551977778'
        settings.address = 'А. Масалиева 44, ТЦ Корона, 3 этаж, Osh, Kyrgyzstan'
        settings.instagram = 'https://www.instagram.com/edupoint.ec/'
        settings.telegram = 'https://t.me/edupoint_ec'
        settings.save()

        # 2. Categories with correct flags
        cat_kr, _ = Category.objects.get_or_create(
            slug='korean',
            defaults={
                'name': 'Корейский язык',
                'language_code': 'korean',
                'flag_emoji': '🇰🇷',
                'description': 'Основное направление Edu Point. 6 уровней обучения по 2 месяца. Подготовка к TOPIK, гранты и визы в Южную Корею.',
                'order': 1
            }
        )
        cat_en, _ = Category.objects.get_or_create(
            slug='english',
            defaults={
                'name': 'Английский язык',
                'language_code': 'english',
                'flag_emoji': '🇬🇧',
                'description': 'Общий английский, разговорный клуб и подготовка к IELTS (6 уровней по 2 месяца).',
                'order': 2
            }
        )
        cat_de, _ = Category.objects.get_or_create(
            slug='german',
            defaults={
                'name': 'Немецкий язык',
                'language_code': 'german',
                'flag_emoji': '🇩🇪',
                'description': 'Курсы немецкого языка для программы Ausbildung, учёбы и работы в Германии (6 уровней по 2 месяца).',
                'order': 3
            }
        )
        cat_cn, _ = Category.objects.get_or_create(
            slug='chinese',
            defaults={
                'name': 'Китайский язык',
                'language_code': 'chinese',
                'flag_emoji': '🇨🇳',
                'description': 'Мандарин с нуля, иероглифика, подготовка к HSK (6 уровней по 2 месяца).',
                'order': 4
            }
        )

        # 3. Teachers
        t1, _ = Teacher.objects.get_or_create(
            name='Ким Мин Сон',
            defaults={
                'position': 'Главный преподаватель корейского языка',
                'experience_years': 12,
                'education': 'Сеульский Национальный Университет (SNU)',
                'languages': 'Корейский (носитель), Русский',
                'bio': 'Эксперт по подготовке к TOPIK I & II с гарантированным выходом на уровни 3-6.',
                'order': 1
            }
        )
        t2, _ = Teacher.objects.get_or_create(
            name='Алина Сергеева',
            defaults={
                'position': 'Старший преподаватель IELTS',
                'experience_years': 8,
                'education': 'Международный университет, CELTA',
                'languages': 'Английский (C2 / IELTS 8.5)',
                'bio': 'Специалист по подсистемам Writing и Speaking для IELTS.',
                'order': 2
            }
        )
        t3, _ = Teacher.objects.get_or_create(
            name='Максим Шмидт',
            defaults={
                'position': 'Преподаватель немецкого языка',
                'experience_years': 10,
                'education': 'Марбургский университет (Германия)',
                'languages': 'Немецкий (носитель), Русский, Английский',
                'bio': 'Специализируется на подготовке студентов к Ausbildung и TestDaF / Goethe.',
                'order': 3
            }
        )

        # 4. Courses (2500 сом/месяц, 6 уровней по 2 месяца с проходным тестом)
        Course.objects.filter(category=cat_kr).update(price=2500)
        c1, _ = Course.objects.get_or_create(
            slug='korean-level-1-2',
            defaults={
                'category': cat_kr,
                'teacher': t1,
                'name': 'Корейский язык (Курс 1 из 6) — Хангыль и Базовая Грамматика',
                'short_description': 'Продолжительность: 2 месяца. В конце 2-го месяца сдаётся проходной тест для перехода на следующий уровень.',
                'description': (
                    '<p><strong>Система обучения:</strong> Вся программа состоит из 6 последовательных курсов. '
                    'Длительность одного курса составляет 2 месяца. После прохождения каждых 2 месяцев студенты сдают '
                    'проходной тест для подведения итогов и перехода на следующий уровень.</p>'
                    '<ul>'
                    '<li>Оплата: 2500 сом / месяц</li>'
                    '<li>Всего курсов в программе: 6 курсов</li>'
                    '<li>Длительность курса: 2 месяца</li>'
                    '<li>Итоговый контроль: Проходной тест после каждого курса</li>'
                    '</ul>'
                ),
                'level': 'beginner',
                'duration': '2 месяца (1 курс из 6)',
                'lessons_per_week': 3,
                'price': 2500,
                'is_featured': True,
            }
        )
        c1.price = 2500
        c1.save()

        c2, _ = Course.objects.get_or_create(
            slug='ielts-preparation-course',
            defaults={
                'category': cat_en,
                'teacher': t2,
                'name': 'Английский язык & IELTS (Курс 1 из 6)',
                'short_description': 'Продолжительность одного курса — 2 месяца. Проходной тест в конце каждого 2-месячного блока.',
                'description': (
                    '<p>Полный курс подготовки от уровня A1 до IELTS 7.0+. Программа разбита на 6 курсов по 2 месяца. '
                    'По завершении 2 месяцев проводится проходной тест.</p>'
                    '<p><strong>Оплата:</strong> 2500 сом в месяц.</p>'
                ),
                'level': 'intermediate',
                'duration': '2 месяца (1 курс из 6)',
                'lessons_per_week': 3,
                'price': 2500,
                'is_featured': True,
            }
        )
        c2.price = 2500
        c2.save()

        c3, _ = Course.objects.get_or_create(
            slug='german-a1-b1-ausbildung',
            defaults={
                'category': cat_de,
                'teacher': t3,
                'name': 'Немецкий язык (Курс 1 из 6) для Ausbildung и Goethe',
                'short_description': 'Продолжительность: 2 месяца. Проходной тест после 2 месяцев учебы.',
                'description': (
                    '<p>Подготовка для работы и учебы в Германии по программе Ausbildung. 6 уровней по 2 месяца. '
                    'Стоимость: 2500 сом/месяц. После каждого 2-месячного курса сдается обязательный проходной тест.</p>'
                ),
                'level': 'beginner',
                'duration': '2 месяца (1 курс из 6)',
                'lessons_per_week': 3,
                'price': 2500,
                'is_featured': True,
            }
        )
        c3.price = 2500
        c3.save()

        c4, _ = Course.objects.get_or_create(
            slug='chinese-hsk-course',
            defaults={
                'category': cat_cn,
                'teacher': t1,
                'name': 'Китайский язык & HSK (Курс 1 из 6)',
                'short_description': 'Продолжительность: 2 месяца. Проходной тест после 2 месяцев учебы.',
                'description': '<p>Изучение мандаринского диалекта и иероглифики. 6 уровней по 2 месяца. Оплата 2500 сом/месяц.</p>',
                'level': 'beginner',
                'duration': '2 месяца (1 курс из 6)',
                'lessons_per_week': 3,
                'price': 2500,
                'is_featured': False,
            }
        )
        c4.price = 2500
        c4.save()

        # 5. Exams (2500 сом/месяц)
        Exam.objects.filter(name='topik').update(price=2500)
        Exam.objects.filter(name='ielts').update(price=2500)
        Exam.objects.filter(name='goethe').update(price=2500)

        # 6. Featured News Item — Paichai University Signing (Kyrgyz language)
        news_paichai, created = NewsPost.objects.get_or_create(
            slug='paichai-university-official-agreement-2026',
            defaults={
                'title': 'Биз Paichai University 🇰🇷 менен расмий келишимге кол койдук!',
                'excerpt': 'Мындан ары биздин студенттер үчүн Кореянын алдыңкы университеттеринин биринде билим алууга чоң мүмкүнчүлүк ачылды!',
                'content': (
                    '<p><strong>Биз Paichai University 🇰🇷 менен расмий келишимге кол койдук!</strong><br>'
                    'Бул кызматташтыкка абдан кубанычтабыз.</p>'
                    '<p>Мындан ары биздин студенттер үчүн дагы бир чоң мүмкүнчүлүк ачылды:</p>'
                    '<ul>'
                    '<li>✨ Кореянын алдыңкы университеттеринин биринде билим алуу</li>'
                    '<li>✨ гранттар жана жеңилдиктер</li>'
                    '<li>✨ заманбап кампус жана эл аралык чөйрө</li>'
                    '<li>✨ келечегиңди курууга реалдуу мүмкүнчүлүк</li>'
                    '</ul>'
                    '<p>📣 <strong>Студенттерди жана абитуриенттерди Кореяда окуу тууралуу толук маалымат алууга, суроолорун берүүгө жана мүмкүнчүлүктү колдон чыгарбоого чакырабыз.</strong></p>'
                    '<p style="font-size:1.15rem;color:#DC2626;font-weight:700;">Бүгүн кадам ташта — эртең Кореяда окуган студент сен бол! 🇰🇷✨</p>'
                ),
                'is_published': True,
            }
        )
        if os.path.exists(r'c:\Users\TechLine\Desktop\б\EduPoint\media\gallery\paichai_1.jpg'):
            news_paichai.image = 'gallery/paichai_1.jpg'
            news_paichai.save()

        # 7. Gallery items from user photos
        gallery_data = [
            ('Paichai University Келишим', 'gallery/paichai_1.jpg', 'students'),
            ('Paichai University Кампус', 'gallery/paichai_2.jpg', 'students'),
            ('Учебный процесс Edu Point', 'gallery/process_2.jpg', 'classes'),
            ('Обучение в классах', 'gallery/process_3.jpg', 'classes'),
            ('Выдача сертификатов выпускникам', 'gallery/certificates_1.jpg', 'events'),
            ('Вручение сертификатов TOPIK', 'gallery/certificates_2.jpg', 'events'),
            ('Университет Songho Корея', 'gallery/universities_songho-university-1.jpg', 'students'),
            ('Студенты в Корее', 'gallery/universities_songho-university-2.jpg', 'students'),
            ('Eid Mubarak Мероприятие', 'gallery/events_aid-mubarak.jpg', 'events'),
        ]

        for title, path, cat in gallery_data:
            if os.path.exists(os.path.join(r'c:\Users\TechLine\Desktop\б\EduPoint\media', path)):
                GalleryImage.objects.get_or_create(
                    title=title,
                    defaults={'image': path, 'category': cat}
                )

        self.stdout.write(self.style.SUCCESS('Данные успешно обновлены!'))
