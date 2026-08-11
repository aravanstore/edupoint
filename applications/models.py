from django.db import models
from django.conf import settings
from django.utils import timezone

# Дни недели (совпадает с lms.Group.DAYS — единый формат кодов)
DAYS = [
    ('mon', 'Понедельник'),
    ('tue', 'Вторник'),
    ('wed', 'Среда'),
    ('thu', 'Четверг'),
    ('fri', 'Пятница'),
    ('sat', 'Суббота'),
    ('sun', 'Воскресенье'),
]
DAY_LABELS = dict(DAYS)


class Branch(models.Model):
    """Филиал учебного центра."""
    name = models.CharField('Название', max_length=200, unique=True)
    address = models.CharField('Адрес', max_length=300, blank=True)
    is_active = models.BooleanField('Активен', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class GroupSet(models.Model):
    """Набор групп — набор/приём учеников на конкретный курс.

    Ресепшен создаёт набор (курс + преподаватель + расписание + места),
    набирает заявки и при необходимости создаёт из набора учебную группу.
    """
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('closed', 'Закрыт'),
        ('archived', 'Архив'),
    ]

    name = models.CharField('Название набора', max_length=200, blank=True,
                            help_text='Пусто — сгенерируется автоматически')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE,
                               related_name='group_sets', verbose_name='Курс')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='group_sets',
                                verbose_name='Преподаватель')
    days = models.CharField('Дни занятий', max_length=100, blank=True,
                            help_text='Коды дней через запятую: mon,wed,fri')
    start_time = models.TimeField('Начало', null=True, blank=True)
    end_time = models.TimeField('Конец', null=True, blank=True)
    start_date = models.DateField('Дата старта группы', null=True, blank=True)
    capacity = models.PositiveIntegerField('Максимум мест', null=True, blank=True,
                                           help_text='Сколько заявок принимаем (пусто — без лимита)')
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='group_sets', verbose_name='Филиал')
    group = models.ForeignKey('lms.Group', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='group_set', verbose_name='Созданная группа')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='open')
    notified_80 = models.BooleanField('Уведомлено о 80%', default=False)
    notified_90 = models.BooleanField('Уведомлено о 90%', default=False)
    notified_100 = models.BooleanField('Уведомлено о 100%', default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='group_sets_created',
                                   verbose_name='Создал')
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    class Meta:
        verbose_name = 'Набор группы'
        verbose_name_plural = 'Наборы групп'
        ordering = ['-created_at']

    def __str__(self):
        return self.name or f'Набор: {self.course}'

    def save(self, *args, **kwargs):
        if not self.name:
            parts = [self.course.name]
            if self.start_date:
                parts.append(f'старт {self.start_date.strftime("%d.%m.%Y")}')
            self.name = ' — '.join(parts)
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Расписание
    # ------------------------------------------------------------------
    def days_codes(self):
        return [d.strip() for d in self.days.split(',') if d.strip()]

    def days_display(self):
        return ', '.join(DAY_LABELS.get(c, c) for c in self.days_codes())

    def time_display(self):
        if self.start_time and self.end_time:
            return f'{self.start_time.strftime("%H:%M")}–{self.end_time.strftime("%H:%M")}'
        if self.start_time:
            return self.start_time.strftime('%H:%M')
        return '—'

    def schedule_display(self):
        parts = []
        if self.days_display():
            parts.append(self.days_display())
        parts.append(self.time_display())
        return ', '.join(parts)

    # ------------------------------------------------------------------
    # Места и заполняемость
    # ------------------------------------------------------------------
    def reserved_count(self):
        """Заявки, занимающие места (все, кроме отказа и потерянного лида)."""
        return self.applications.exclude(status__in=['rejected', 'lost']).count()

    def is_full(self):
        if not self.capacity:
            return False
        return self.reserved_count() >= self.capacity

    def seats_left(self):
        if not self.capacity:
            return None
        return max(self.capacity - self.reserved_count(), 0)

    def fill_percent(self):
        if not self.capacity:
            return 0
        return round(self.reserved_count() / self.capacity * 100)

    def waitlist_count(self):
        return self.waitlist.count()

    def can_apply(self):
        return self.status == 'open' and not self.is_full()


class StudentApplication(models.Model):
    """Заявка на запись в учебный центр (воронка CRM)."""
    STATUS_CHOICES = [
        ('new', 'Новая заявка'),
        ('contacted', 'Связались'),
        ('test', 'Записан на тест'),
        ('test_passed', 'Тест пройден'),
        ('enrolled', 'Зачислен'),
        ('rejected', 'Отказался'),
        ('lost', 'Потерянный лид'),
    ]
    # Статусы, которые занимают место в наборе
    ACTIVE_STATUSES = ('new', 'contacted', 'test', 'test_passed', 'enrolled')
    CLOSED_STATUSES = ('rejected', 'lost')
    STATUS_DICT = dict(STATUS_CHOICES)

    SOURCE_CHOICES = [
        ('instagram', 'Instagram'),
        ('telegram', 'Telegram'),
        ('google', 'Google'),
        ('facebook', 'Facebook'),
        ('tiktok', 'TikTok'),
        ('referral', 'Рекомендация'),
        ('other', 'Другое'),
    ]
    SOURCE_DICT = dict(SOURCE_CHOICES)

    LEVEL_CHOICES = [
        ('zero', 'С нуля'),
        ('beginner', 'Начальный'),
        ('elementary', 'Элементарный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый'),
    ]

    name = models.CharField('Имя', max_length=200)
    phone = models.CharField('Телефон', max_length=50)
    age = models.PositiveIntegerField('Возраст', null=True, blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='applications', verbose_name='Курс')
    group_set = models.ForeignKey(GroupSet, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='applications', verbose_name='Набор')
    source = models.CharField('Источник заявки', max_length=20, choices=SOURCE_CHOICES,
                              default='other')
    language_level = models.CharField('Уровень языка', max_length=20, choices=LEVEL_CHOICES,
                                      default='zero')
    comment = models.TextField('Комментарий', blank=True)
    notes = models.TextField('Заметки CRM', blank=True)
    student = models.ForeignKey('lms.StudentProfile', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='applications',
                                verbose_name='Созданный ученик')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='applications_created',
                                   verbose_name='Кто создал')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='applications_updated',
                                   verbose_name='Кто обновил')
    status_changed_at = models.DateTimeField('Статус изменён', null=True, blank=True)
    created_at = models.DateTimeField('Дата заявки', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки на запись'
        ordering = ['-created_at']

    def __str__(self):
        set_name = f' → {self.group_set}' if self.group_set else ''
        return f'{self.name} — {self.phone} ({self.created_at.strftime("%d.%m.%Y")}){set_name}'

    def is_active_status(self):
        return self.status in self.ACTIVE_STATUSES

    def masked_name(self):
        """ФИО для публичного показа: первые 3 буквы имени + ***, фамилия скрыта."""
        parts = self.name.split()
        if not parts:
            return '***'
        masked_first = parts[0][:3] + '***'
        if len(parts) > 1:
            return f'{masked_first} ***'
        return masked_first

    def masked_phone(self):
        """Телефон для публичного показа: видны только последние 2 цифры."""
        total_digits = sum(1 for c in self.phone if c.isdigit())
        keep_from = total_digits - 2
        result = []
        digit_index = 0
        for ch in self.phone:
            if ch.isdigit():
                result.append(ch if digit_index >= keep_from else '*')
                digit_index += 1
            else:
                result.append(ch)
        return ''.join(result)


class ApplicationStatusHistory(models.Model):
    """История смены статусов заявки — для воронки и конверсии."""
    application = models.ForeignKey(StudentApplication, on_delete=models.CASCADE,
                                    related_name='status_history', verbose_name='Заявка')
    old_status = models.CharField('Было', max_length=20, blank=True)
    new_status = models.CharField('Стало', max_length=20)
    note = models.CharField('Примечание', max_length=300, blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='application_status_history',
                                   verbose_name='Кто изменил')
    created_at = models.DateTimeField('Время', auto_now_add=True)

    class Meta:
        verbose_name = 'Изменение статуса'
        verbose_name_plural = 'История статусов заявок'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.application} — {self.new_status}'

    def new_status_label(self):
        return StudentApplication.STATUS_DICT.get(self.new_status, self.new_status)


class WaitlistEntry(models.Model):
    """Лист ожидания для заполненных наборов."""
    group_set = models.ForeignKey(GroupSet, on_delete=models.CASCADE,
                                  related_name='waitlist', verbose_name='Набор')
    name = models.CharField('Имя', max_length=200)
    phone = models.CharField('Телефон', max_length=50)
    note = models.CharField('Примечание', max_length=300, blank=True)
    notified = models.BooleanField('Уведомлён об освобождении места', default=False)
    created_at = models.DateTimeField('Добавлен', auto_now_add=True)

    class Meta:
        verbose_name = 'Запись листа ожидания'
        verbose_name_plural = 'Лист ожидания'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.phone} ({self.group_set})'


class SpendEntry(models.Model):
    """Расходы на маркетинг по источникам — для стоимости лида."""
    source = models.CharField('Источник', max_length=20, choices=StudentApplication.SOURCE_CHOICES)
    month = models.DateField('Месяц', help_text='Первое число месяца')
    amount = models.DecimalField('Сумма (сом)', max_digits=10, decimal_places=2, default=0)
    note = models.CharField('Примечание', max_length=300, blank=True)
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)

    class Meta:
        verbose_name = 'Расход на маркетинг'
        verbose_name_plural = 'Расходы на маркетинг'
        ordering = ['-month']
        unique_together = ('source', 'month')

    def __str__(self):
        return f'{self.get_source_display()} — {self.month:%m.%Y}: {self.amount} сом'
