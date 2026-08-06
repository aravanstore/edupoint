from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Review(models.Model):
    """Отзывы студентов."""
    name = models.CharField('Имя', max_length=200)
    photo = models.ImageField('Фото', upload_to='reviews/', blank=True)
    course = models.ForeignKey('courses.Course', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='reviews', verbose_name='Курс')
    text = models.TextField('Отзыв')
    rating = models.PositiveIntegerField(
        'Оценка', default=5,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    is_approved = models.BooleanField('Опубликован', default=False)
    created_at = models.DateTimeField('Дата', auto_now_add=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['order', '-created_at']

    def __str__(self):
        return f'{self.name} — {self.rating}⭐'

    def get_stars_range(self):
        """Возвращает range для рендеринга звёзд в шаблоне."""
        return range(self.rating)

    def get_empty_stars_range(self):
        return range(5 - self.rating)
