import os
import sys
import django

sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edupoint.settings')
django.setup()

from games.models import Game, GameRoom

GAMES_DATA = [
    {
        'slug': 'mafia',
        'title': 'Мафия Языковедов',
        'subtitle': 'Детективная игра на выявление Мистер Мафии среди знатоков слов!',
        'icon': '🕵️‍♂️',
        'category': 'mafia',
        'order': 1,
        'default_rounds': 5,
        'default_time_sec': 30,
        'description': 'Детективная ролевая миссия! Один из игроков — скрытая "Мафия", дающий неверные переводы. Команда допрашивает участников, сверяет переводы слов и голосованием определяет нарушителя!',
        'rules': [
            'В начале раунда распределяются роли: Знатоки и Мафия.',
            'Мафия пытается запутать других, давая обманные варианты слов.',
            'Игроки голосуют за подозреваемого мафиози после обсуждения.'
        ]
    },
    {
        'slug': 'wordle',
        'title': 'Отгадай слово',
        'subtitle': 'Интеллектуальная головоломка: угадай загаданное слово по подсказкам',
        'icon': '🔠',
        'category': 'vocab',
        'order': 2,
        'default_rounds': 10,
        'default_time_sec': 45,
        'description': 'Классический угадайка слов! Вам даётся определение или контекст слова на корейском/английском. Собирайте слово по буквам за минимальное количество попыток!',
        'rules': [
            'Внимательно прочтите подсказку или картинку.',
            'Вводите буквы или слово целиком.',
            'Получайте бонусные очки за отгадку без использования лишних подсказок.'
        ]
    },
    {
        'slug': 'quiz-master',
        'title': 'Выбери правильный вариант',
        'subtitle': 'Динамичный спринт с выбором точного значения и перевода',
        'icon': '🎯',
        'category': 'vocab',
        'order': 3,
        'default_rounds': 15,
        'default_time_sec': 15,
        'description': 'Скоростной баттл на точность слов. За отведённые секунды выбирайте 1 правильный вариант из 4 предложенных.',
        'rules': [
            'Быстро читайте слово в карточке.',
            'Нажимайте 1 из 4 вариантов.',
            'Серия правильных ответов активирует Множитель Очков x2, x3!'
        ]
    },
    {
        'slug': 'scramble',
        'title': 'Собери слово из букв',
        'subtitle': 'Расставь перепутанные буквы и слоги в правильном порядке',
        'icon': '🧩',
        'category': 'vocab',
        'order': 4,
        'default_rounds': 10,
        'default_time_sec': 25,
        'description': 'Буквы в слове перепутались! Ваша задача — кликать по карточкам букв, восстанавливая исходное слово.',
        'rules': [
            'Слово раздроблено на отдельные буквы.',
            'Нажимайте на буквы по порядку составления слова.',
            'Используйте кнопку "Очистить" при ошибке.'
        ]
    },
    {
        'slug': 'speed-typing',
        'title': 'Скоростной набор',
        'subtitle': 'Проверь скорость клавиатуры на иностранных языках!',
        'icon': '⚡',
        'category': 'typing',
        'order': 5,
        'default_rounds': 10,
        'default_time_sec': 20,
        'description': 'Соревнование на скорость печати слов на корейском, английском и немецком языках. Набирайте без ошибок!',
        'rules': [
            'На экране появляется слово.',
            'Печатайте его в поле ввода и нажимайте Enter.',
            'Чем быстрее ввод, тем больше бонус за скорость (WPM).'
        ]
    },
    {
        'slug': 'memory-match',
        'title': 'Карточки Парочки',
        'subtitle': 'Развивай визуальную и словарную память — ищи парные карты!',
        'icon': '🎴',
        'category': 'typing',
        'order': 6,
        'default_rounds': 8,
        'default_time_sec': 40,
        'description': 'Тренировка памяти и запаса! Открывайте закрытые карточки и находите пары "Иностранное слово — Его перевод".',
        'rules': [
            'На поле разложены рубашкой вверх карточки.',
            'Открывайте по 2 карточки за ход.',
            'Совпадение пары даёт очки и оставляет карты открытыми.'
        ]
    },
    {
        'slug': 'grammar-battle',
        'title': 'Грамматический Баттл',
        'subtitle': 'Найди и исправь грамматическую ошибку в предложении',
        'icon': '🏛️',
        'category': 'grammar',
        'order': 7,
        'default_rounds': 12,
        'default_time_sec': 25,
        'description': 'Настоящий вызов экспертам грамматики! Проверьте предложение на частицы корейского языка (은/는, 이/가), артикли английского или падежи немецкого.',
        'rules': [
            'Внимательно прочитайте предложение.',
            'Укажите ошибочное слово или выберите исправление.',
            'Получайте очки за безупречный грамматический разбор.'
        ]
    },
    {
        'slug': 'sound-master',
        'title': 'Аудио Викторина',
        'subtitle': 'Натренируй слух на правильное произношение слов',
        'icon': '🎧',
        'category': 'vocab',
        'order': 8,
        'default_rounds': 10,
        'default_time_sec': 20,
        'description': 'Слушайте произношение слова голосом и выбирайте соответствующее значение среди вариантов.',
        'rules': [
            'Нажмите кнопку "Воспроизвести звук".',
            'Внимательно прослушайте произношение.',
            'Выберите верный перевод слова из списка.'
        ]
    },
    {
        'slug': 'context-quiz',
        'title': 'Контекстный Ассоциатор',
        'subtitle': 'Вставь наиболее подходящее слово в текст по смыслу',
        'icon': '🔮',
        'category': 'grammar',
        'order': 9,
        'default_rounds': 10,
        'default_time_sec': 30,
        'description': 'Дан отрывок предложения с пропуском `[ ? ]`. Определите логику контекста и вставьте нужное слово.',
        'rules': [
            'Прочтите предложение полностью.',
            'Поймите контекст ситуации.',
            'Выберите наиболее подходящее по смыслу слово.'
        ]
    },
    {
        'slug': 'academic-duel',
        'title': 'Академический Дуэль',
        'subtitle': 'Марафон вопросов уровня TOPIK II, IELTS 7.0+ и Goethe C1',
        'icon': '🏆',
        'category': 'exam',
        'order': 10,
        'default_rounds': 20,
        'default_time_sec': 30,
        'description': 'Самая длинная и престижная игра для сильнейших! 20 сложных вопросов из билетов международной сертификации.',
        'rules': [
            'Участвуйте в марафоне из 20 раундов.',
            'Каждый верный ответ повышает рейтинг в общегодовом Подиуме.',
            'Победитель получает виртуальный кубок Академии Edu Point!'
        ]
    }
]

print("Seeding 10 Mini-games into database...")

for g_data in GAMES_DATA:
    game, created = Game.objects.update_or_create(
        slug=g_data['slug'],
        defaults={
            'title': g_data['title'],
            'subtitle': g_data['subtitle'],
            'icon': g_data['icon'],
            'category': g_data['category'],
            'order': g_data['order'],
            'default_rounds': g_data['default_rounds'],
            'default_time_sec': g_data['default_time_sec'],
            'description': g_data['description'],
            'rules_json': str(g_data['rules']),
            'is_active': True,
        }
    )
    status = "Created" if created else "Updated"
    print(f"[{status}] {game.icon} {game.title}")

    # Generate 4 rooms for each game
    for r_num in range(1, 5):
        room, r_created = GameRoom.objects.get_or_create(
            game=game,
            room_number=r_num,
            defaults={
                'name': f'Комната #{r_num}',
                'host_name': 'Свободна (нажмите стать хостом)',
                'difficulty': 'medium',
                'max_rounds': game.default_rounds,
                'round_time_sec': game.default_time_sec,
            }
        )

print("✅ Successfully seeded 10 mini-games and 40 rooms!")
