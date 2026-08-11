from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify


class UserProfile(models.Model):
    """Профиль пользователя — определяет роль в системе."""
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('reception', 'Ресепшен'),
        ('teacher', 'Учитель'),
        ('student', 'Ученик'),
        ('parent', 'Родитель'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='profile', verbose_name='Пользователь')
    role = models.CharField('Роль', max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField('Телефон', max_length=50, blank=True)
    avatar = models.ImageField('Аватар', upload_to='profiles/avatars/', blank=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'

    @classmethod
    def role_for(cls, user):
        """Возвращает роль пользователя. Суперпользователь всегда admin."""
        if not user.is_authenticated:
            return None
        if user.is_superuser:
            return 'admin'
        try:
            return user.profile.role
        except UserProfile.DoesNotExist:
            return None


class Book(models.Model):
    """Книга учебного курса (например, Korean Book 1 из 6)."""
    category = models.ForeignKey('courses.Category', on_delete=models.CASCADE,
                                 related_name='books', verbose_name='Язык')
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('URL', unique=True, blank=True)
    order = models.PositiveIntegerField('Порядок (номер книги)', default=1)
    duration_months = models.PositiveIntegerField('Длительность (месяцев)', default=2)
    price_per_month = models.DecimalField('Цена (сом/мес)', max_digits=8, decimal_places=0, default=2500)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['category__order', 'order']

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            lang = self.category.language_code if self.category else 'book'
            self.slug = f'{lang}-book-{self.order}'
        super().save(*args, **kwargs)


class Group(models.Model):
    """Учебная группа (не класс): курс + книга + время + дни."""
    DAYS = [
        ('mon', 'Понедельник'),
        ('tue', 'Вторник'),
        ('wed', 'Среда'),
        ('thu', 'Четверг'),
        ('fri', 'Пятница'),
        ('sat', 'Суббота'),
        ('sun', 'Воскресенье'),
    ]
    STATUS_CHOICES = [
        ('active', 'Активная'),
        ('closed', 'Закрыта'),
    ]
    name = models.CharField('Название группы', max_length=200)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE,
                               related_name='lms_groups', verbose_name='Курс')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='lms_groups',
                                verbose_name='Преподаватель')
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='groups', verbose_name='Книга')
    days = models.CharField('Дни занятий', max_length=100, blank=True,
                            help_text='Коды дней через запятую: mon,wed,fri')
    start_time = models.TimeField('Начало', null=True, blank=True)
    end_time = models.TimeField('Конец', null=True, blank=True)
    room = models.CharField('Аудитория', max_length=50, blank=True)
    capacity = models.PositiveIntegerField('Лимит учеников', null=True, blank=True,
                                           help_text='Максимум учеников в группе (пусто — без ограничений)')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='active')
    started_at = models.DateField('Дата начала', null=True, blank=True)
    branch = models.ForeignKey('applications.Branch', on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='lms_groups',
                               verbose_name='Филиал')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['name']

    def __str__(self):
        return self.name

    def days_display(self):
        codes = [d.strip() for d in self.days.split(',') if d.strip()]
        mapping = dict(self.DAYS)
        names = [mapping.get(c, c) for c in codes]
        return ', '.join(names)

    def time_display(self):
        if self.start_time and self.end_time:
            return f'{self.start_time.strftime("%H:%M")}–{self.end_time.strftime("%H:%M")}'
        return '—'

    def student_count(self):
        return self.students.count()

    def is_full(self):
        if not self.capacity:
            return False
        return self.students.count() >= self.capacity

    def seats_left(self):
        if not self.capacity:
            return None
        return max(self.capacity - self.students.count(), 0)


class StudentProfile(models.Model):
    """Ученик учебного центра."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='student_profile', verbose_name='Пользователь')
    group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='students', verbose_name='Группа')
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='students', verbose_name='Текущая книга')
    book_progress = models.PositiveIntegerField('Прогресс книги (%)', default=0,
                                                validators=[MinValueValidator(0), MaxValueValidator(100)])
    parent = models.ForeignKey('ParentProfile', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='children', verbose_name='Родитель')
    phone = models.CharField('Телефон', max_length=50, blank=True)
    parent_phone = models.CharField('Телефон родителя', max_length=50, blank=True)
    birth_date = models.DateField('Дата рождения', null=True, blank=True)
    enrolled_at = models.DateField('Зачислен', auto_now_add=True)
    notes = models.TextField('Заметки', blank=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Ученик'
        verbose_name_plural = 'Ученики'
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def teacher(self):
        return self.group.teacher if self.group else None

    # ------------------------------------------------------------------
    # Оплата и статус
    # ------------------------------------------------------------------
    def payment_for_month(self, month_date):
        return self.payments.filter(
            month__year=month_date.year, month__month=month_date.month
        ).order_by('-paid_at').first()

    def extension_for_month(self, month_date):
        return self.extensions.filter(
            month__year=month_date.year, month__month=month_date.month
        ).order_by('-new_due_date').first()

    def payment_status(self):
        """Возвращает (status, due_date): paid / pending / frozen / none."""
        today = timezone.localdate()
        month_start = today.replace(day=1)
        payment = self.payment_for_month(month_start)
        if payment and payment.is_confirmed:
            return ('paid', payment.month)
        extension = self.extension_for_month(month_start)
        due = extension.new_due_date if extension and extension.new_due_date >= month_start else month_start
        if today <= due:
            return ('pending', due)
        if payment and not payment.is_confirmed:
            return ('frozen', due)
        return ('frozen', due)

    def is_frozen(self):
        status, _ = self.payment_status()
        return status == 'frozen'

    def debt_amount(self):
        """Сумма задолженности: текущий месяц (цена книги) если не оплачен."""
        if not self.is_frozen():
            return 0
        price = self.book.price_per_month if self.book else 2500
        return price

    # ------------------------------------------------------------------
    # Статистика
    # ------------------------------------------------------------------
    def average_grade(self):
        grades = self.grades.all()
        if not grades:
            return None
        return round(sum(g.value for g in grades) / len(grades), 1)

    def attendance_stats(self):
        records = self.attendance_records.all()
        total = records.count()
        if total == 0:
            return {'total': 0, 'present': 0, 'absent': 0, 'late': 0, 'percent': None}
        present = records.filter(status='present').count()
        absent = records.filter(status='absent').count()
        late = records.filter(status='late').count()
        attended = present + late
        percent = round(attended / total * 100)
        return {'total': total, 'present': present, 'absent': absent,
                'late': late, 'percent': percent}

    def book_ladder(self):
        """Лестница книг с прогрессом: текущая разблокирована, следующие — Locked."""
        books = Book.objects.filter(category=self.book.category if self.book else None, is_active=True).order_by('order')
        ladder = []
        current_order = self.book.order if self.book else 0
        for book in books:
            if book.order < current_order:
                state = 'done'
            elif book.order == current_order:
                state = 'current'
            else:
                state = 'locked'
            ladder.append({'book': book, 'state': state})
        return ladder


class ParentProfile(models.Model):
    """Родитель. Может иметь несколько детей (StudentProfile.parent)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='parent_profile', verbose_name='Пользователь')
    phone = models.CharField('Телефон', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Родитель'
        verbose_name_plural = 'Родители'
        ordering = ['user__first_name', 'user__last_name']

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class TeacherProfile(models.Model):
    """Связка пользователя-учителя с публичной карточкой Teacher."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='teacher_profile', verbose_name='Пользователь')
    teacher = models.OneToOneField('teachers.Teacher', on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='teacher_profile',
                                   verbose_name='Карточка преподавателя')
    phone = models.CharField('Телефон', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Учитель (аккаунт)'
        verbose_name_plural = 'Учителя (аккаунты)'

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Grade(models.Model):
    """Оценка 0-10."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE,
                                related_name='grades', verbose_name='Ученик')
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='grades', verbose_name='Группа')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='lms_grades',
                                verbose_name='Учитель')
    value = models.PositiveSmallIntegerField('Оценка (0-10)', validators=[MinValueValidator(0), MaxValueValidator(10)])
    date = models.DateField('Дата', default=timezone.localdate)
    comment = models.CharField('Комментарий', max_length=300, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        ordering = ['-date', '-created_at']
        unique_together = ('student', 'date')

    def __str__(self):
        return f'{self.student} — {self.value} ({self.date})'


class Attendance(models.Model):
    """Посещаемость: присутствовал / отсутствовал / опоздал."""
    STATUS_CHOICES = [
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE,
                                related_name='attendance_records', verbose_name='Ученик')
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='attendance_records', verbose_name='Группа')
    date = models.DateField('Дата', default=timezone.localdate)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='present')
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        ordering = ['-date']
        unique_together = ('student', 'date')

    def __str__(self):
        return f'{self.student} — {self.get_status_display()} ({self.date})'


class Homework(models.Model):
    """Домашнее задание для группы."""
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='homeworks', verbose_name='Группа')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='lms_homeworks',
                                verbose_name='Учитель')
    title = models.CharField('Заголовок', max_length=300)
    description = models.TextField('Задание', blank=True)
    photo = models.ImageField('Фото', upload_to='homeworks/', blank=True)
    video = models.URLField('Видео', blank=True)
    file = models.FileField('Файл (PDF и др.)', upload_to='homeworks/', blank=True)
    due_date = models.DateField('Срок сдачи', null=True, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} — {self.group}'


class HomeworkSubmission(models.Model):
    """Ответ ученика на домашнее задание."""
    homework = models.ForeignKey(Homework, on_delete=models.CASCADE,
                                 related_name='submissions', verbose_name='Задание')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE,
                                related_name='submissions', verbose_name='Ученик')
    text = models.TextField('Текст ответа', blank=True)
    photo = models.ImageField('Фото ответа', upload_to='homework_submissions/', blank=True)
    submitted_at = models.DateTimeField('Отправлено', auto_now_add=True)
    is_late = models.BooleanField('Просрочено', default=False)

    class Meta:
        verbose_name = 'Ответ на задание'
        verbose_name_plural = 'Ответы на задания'
        ordering = ['-submitted_at']
        unique_together = ('homework', 'student')

    def __str__(self):
        return f'{self.student} → {self.homework.title}'


class Payment(models.Model):
    """Оплата за месяц."""
    METHOD_CHOICES = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        ('transfer', 'Перевод'),
        ('other', 'Другое'),
    ]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE,
                                related_name='payments', verbose_name='Ученик')
    month = models.DateField('Месяц оплаты', help_text='Первое число месяца, за который оплата')
    amount = models.DecimalField('Сумма (сом)', max_digits=8, decimal_places=0, default=2500)
    method = models.CharField('Метод', max_length=20, choices=METHOD_CHOICES, default='cash')
    is_confirmed = models.BooleanField('Подтверждена', default=True)
    note = models.CharField('Примечание', max_length=300, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='payments_created',
                                   verbose_name='Кто принял')
    paid_at = models.DateTimeField('Оплачено', auto_now_add=True)

    class Meta:
        verbose_name = 'Оплата'
        verbose_name_plural = 'Оплаты'
        ordering = ['-month']
        indexes = [models.Index(fields=['student', 'month'])]

    def __str__(self):
        return f'{self.student} — {self.month.strftime("%m.%Y")} ({self.amount} сом)'


class PaymentExtension(models.Model):
    """Отсрочка оплаты (перенос срока) для ученика."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE,
                                related_name='extensions', verbose_name='Ученик')
    month = models.DateField('Месяц', help_text='Месяц, к которому относится отсрочка')
    new_due_date = models.DateField('Новый срок оплаты')
    reason = models.CharField('Причина', max_length=300, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                   null=True, blank=True, related_name='extensions_created',
                                   verbose_name='Кто оформил')
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Отсрочка оплаты'
        verbose_name_plural = 'Отсрочки оплаты'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['student', 'month'])]

    def __str__(self):
        return f'{self.student} — отсрочка до {self.new_due_date}'


class Announcement(models.Model):
    """Объявление. Для группы (group задана) или для всех (group=None)."""
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              null=True, blank=True, related_name='announcements',
                              verbose_name='Группа (пусто — всем)')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                               null=True, blank=True, related_name='announcements',
                               verbose_name='Автор')
    title = models.CharField('Заголовок', max_length=300)
    text = models.TextField('Текст')
    is_active = models.BooleanField('Активно', default=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Notification(models.Model):
    """Внутрисайтовое уведомление для пользователя."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                             related_name='lms_notifications', verbose_name='Получатель')
    text = models.CharField('Текст', max_length=500)
    link = models.CharField('Ссылка', max_length=300, blank=True)
    is_read = models.BooleanField('Прочитано', default=False)
    created_at = models.DateTimeField('Создано', auto_now_add=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} — {self.text[:50]}'


class ActivityLog(models.Model):
    """Журнал действий сотрудников (история изменений)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='lms_activity',
                             verbose_name='Кто')
    action = models.CharField('Действие', max_length=100)
    target = models.CharField('Объект', max_length=300, blank=True)
    details = models.CharField('Детали', max_length=500, blank=True)
    created_at = models.DateTimeField('Время', auto_now_add=True)

    class Meta:
        verbose_name = 'Запись журнала'
        verbose_name_plural = 'Журнал действий'
        ordering = ['-created_at']

    def __str__(self):
        who = self.user.get_full_name() or self.user.username if self.user else '—'
        return f'{who} — {self.action} ({self.created_at:%d.%m.%Y %H:%M})'
