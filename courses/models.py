from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField


class Category(models.Model):
    """Языковые направления (Корейский, Английский, Немецкий, Китайский)."""
    LANGUAGE_CHOICES = [
        ('korean', 'Корейский'),
        ('english', 'Английский'),
        ('german', 'Немецкий'),
        ('chinese', 'Китайский'),
    ]
    FLAG_CHOICES = [
        ('korean', '🇰🇷'),
        ('english', '🇬🇧'),
        ('german', '🇩🇪'),
        ('chinese', '🇨🇳'),
    ]
    name = models.CharField('Название', max_length=100)
    slug = models.SlugField('URL', unique=True)
    language_code = models.CharField('Код языка', max_length=20, choices=LANGUAGE_CHOICES, unique=True)
    flag_emoji = models.CharField('Флаг', max_length=10, default='🌐')
    description = models.TextField('Описание', blank=True)
    image = models.ImageField('Изображение', upload_to='categories/', blank=True)
    color = models.CharField('Цвет (hex)', max_length=7, default='#0EA5E9')
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории языков'
        ordering = ['order']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('courses:language', kwargs={'slug': self.slug})


class Course(models.Model):
    """Курс — конкретная программа обучения."""
    LEVEL_CHOICES = [
        ('beginner', 'Начальный (A1-A2)'),
        ('elementary', 'Элементарный (A2-B1)'),
        ('intermediate', 'Средний (B1-B2)'),
        ('advanced', 'Продвинутый (C1-C2)'),
        ('all', 'Все уровни'),
    ]
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='courses', verbose_name='Язык')
    teacher = models.ForeignKey('teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='courses', verbose_name='Преподаватель')
    name = models.CharField('Название курса', max_length=200)
    slug = models.SlugField('URL', unique=True, blank=True)
    short_description = models.TextField('Краткое описание', max_length=300, blank=True)
    description = RichTextField('Полное описание', blank=True)
    level = models.CharField('Уровень', max_length=20, choices=LEVEL_CHOICES, default='beginner')
    duration = models.CharField('Длительность', max_length=100, default='3 месяца')
    lessons_per_week = models.PositiveIntegerField('Занятий в неделю', default=3)
    price = models.DecimalField('Цена (сом)', max_digits=8, decimal_places=0, default=0)
    image = models.ImageField('Изображение', upload_to='courses/', blank=True)
    is_featured = models.BooleanField('На главной', default=False)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)

    # SEO
    meta_title = models.CharField('SEO: Title', max_length=255, blank=True)
    meta_description = models.TextField('SEO: Description', blank=True)

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['category__order', 'name']

    def __str__(self):
        return f'{self.category.name} — {self.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('courses:detail', kwargs={'slug': self.slug})


class CourseSchedule(models.Model):
    """Расписание занятий для курса."""
    DAY_CHOICES = [
        ('mon', 'Понедельник'),
        ('tue', 'Вторник'),
        ('wed', 'Среда'),
        ('thu', 'Четверг'),
        ('fri', 'Пятница'),
        ('sat', 'Суббота'),
        ('sun', 'Воскресенье'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    day = models.CharField('День', max_length=3, choices=DAY_CHOICES)
    start_time = models.TimeField('Начало')
    end_time = models.TimeField('Конец')
    room = models.CharField('Аудитория', max_length=50, blank=True)

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'

    def __str__(self):
        return f'{self.course.name} — {self.get_day_display()} {self.start_time}'
