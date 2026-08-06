from django.db import models
from django.conf import settings


class Teacher(models.Model):
    """Преподаватель учебного центра."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='teacher_card',
                                verbose_name='Аккаунт (User)')
    name = models.CharField('Имя', max_length=200)
    position = models.CharField('Должность', max_length=200, blank=True, default='Преподаватель')
    photo = models.ImageField('Фото', upload_to='teachers/', blank=True)
    bio = models.TextField('О себе', blank=True)
    experience_years = models.PositiveIntegerField('Опыт (лет)', default=1)
    education = models.CharField('Образование', max_length=300, blank=True)
    languages = models.CharField('Преподаёт языки', max_length=200, blank=True)
    instagram = models.URLField('Instagram', blank=True)
    telegram = models.URLField('Telegram', blank=True)
    is_active = models.BooleanField('Активен', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name
