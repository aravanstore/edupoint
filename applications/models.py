from django.db import models


class StudentApplication(models.Model):
    """Заявки на запись в учебный центр."""
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('contacted', 'Связались'),
        ('enrolled', 'Зачислен'),
        ('rejected', 'Отказ'),
    ]
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
    language_level = models.CharField('Уровень языка', max_length=20, choices=LEVEL_CHOICES, default='zero')
    comment = models.TextField('Комментарий', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('Дата заявки', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки на запись'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.phone} ({self.created_at.strftime("%d.%m.%Y")})'
