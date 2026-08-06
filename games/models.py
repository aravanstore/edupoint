from django.db import models
from django.utils import timezone

class Game(models.Model):
    CATEGORY_CHOICES = [
        ('vocab', 'Словарный запас'),
        ('grammar', 'Грамматика'),
        ('typing', 'Скорость и память'),
        ('mafia', 'Мафия и логика'),
        ('exam', 'Экзамены и дуэли'),
    ]

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=150, verbose_name="Название игры")
    subtitle = models.CharField(max_length=255, verbose_name="Подзаголовок", blank=True)
    icon = models.CharField(max_length=50, default="🎮", verbose_name="Иконка (эмодзи)")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='vocab', verbose_name="Категория")
    description = models.TextField(verbose_name="Описание и правила")
    rules_json = models.TextField(default="[]", help_text="Правила игры в формате JSON массива")
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    default_rounds = models.IntegerField(default=10, verbose_name="Число раундов по умолчанию")
    default_time_sec = models.IntegerField(default=20, verbose_name="Секунд на раунд")
    order = models.IntegerField(default=0, verbose_name="Порядок сортировки")

    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Мини-игра"
        verbose_name_plural = "Мини-игры"

    def __str__(self):
        return f"{self.icon} {self.title}"


class GameRoom(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Легкий (Начинающий A1-A2)'),
        ('medium', 'Средний (B1-B2)'),
        ('hard', 'Продвинутый (C1-C2)'),
        ('mixed', 'Смешанный'),
    ]

    LANGUAGE_CHOICES = [
        ('all', '🌐 Все языки (Смешанный)'),
        ('korean', '🇰🇷 Корейский'),
        ('english', '🇬🇧 Английский'),
        ('german', '🇩🇪 Немецкий'),
        ('chinese', '🇨🇳 Китайский'),
    ]

    STATUS_CHOICES = [
        ('waiting', 'В ожидании игроков'),
        ('in_game', 'Идёт игра'),
        ('finished', 'Завершена / Свободна'),
    ]

    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='rooms', verbose_name="Игра")
    room_number = models.IntegerField(verbose_name="Номер комнаты (1-4)")
    name = models.CharField(max_length=100, verbose_name="Название комнаты")
    host_name = models.CharField(max_length=100, default="Свободна (нажмите стать хостом)", verbose_name="Имя хоста")
    host_session_id = models.CharField(max_length=100, blank=True, null=True, verbose_name="ID сессии хоста")
    is_occupied = models.BooleanField(default=False, verbose_name="Занята")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='waiting', verbose_name="Статус комнаты")
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='easy', verbose_name="Сложность")
    max_rounds = models.IntegerField(default=10, verbose_name="Количество раундов")
    round_time_sec = models.IntegerField(default=20, verbose_name="Время на раунд (сек)")
    max_players = models.IntegerField(default=4, verbose_name="Максимум игроков (2-8)")
    target_language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='korean', verbose_name="Целевой язык")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('game', 'room_number')
        ordering = ['game', 'room_number']
        verbose_name = "Комната игры"
        verbose_name_plural = "Комнаты игр"

    def __str__(self):
        return f"{self.game.title} — Комната #{self.room_number}"

    def reset_room(self):
        """Resets room back to free status after game ends."""
        self.is_occupied = False
        self.status = 'waiting'
        self.host_name = 'Свободна (нажмите стать хостом)'
        self.host_session_id = None
        self.save()
        self.players.all().delete()


class RoomPlayer(models.Model):
    room = models.ForeignKey(GameRoom, on_delete=models.CASCADE, related_name='players')
    player_name = models.CharField(max_length=100, verbose_name="Имя реального игрока")
    session_key = models.CharField(max_length=100, verbose_name="Session Key")
    is_host = models.BooleanField(default=False, verbose_name="Хост")
    is_ready = models.BooleanField(default=True, verbose_name="Готов")
    avatar = models.CharField(max_length=10, default="😎")
    joined_at = models.DateTimeField(default=timezone.now)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['joined_at']
        unique_together = ('room', 'session_key')
        verbose_name = "Игрок комнаты"
        verbose_name_plural = "Игроки комнат"

    def __str__(self):
        return f"{self.player_name} ({'Хост' if self.is_host else 'Игрок'}) in {self.room}"


class GameResult(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='results')
    room_number = models.IntegerField(default=1)
    player_name = models.CharField(max_length=100, verbose_name="Имя игрока")
    score = models.IntegerField(default=0, verbose_name="Очки за матч")
    correct_answers = models.IntegerField(default=0, verbose_name="Правильных ответов")
    total_answers = models.IntegerField(default=0, verbose_name="Всего ответов")
    is_win = models.BooleanField(default=False, verbose_name="Победа в матче (1-е место)")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-is_win', '-score', '-created_at']
        verbose_name = "Результат игры"
        verbose_name_plural = "Результаты игр"

    def __str__(self):
        return f"{self.player_name}: {self.score} очков ({self.game.title})"
