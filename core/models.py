from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField


class SiteSettings(models.Model):
    """Глобальные настройки сайта — управляются через Admin."""
    phone = models.CharField('Телефон', max_length=50, default='+996 700 995 577')
    whatsapp = models.CharField('WhatsApp', max_length=50, default='996700995577')
    email = models.EmailField('Email', blank=True)
    address = models.CharField('Адрес', max_length=255, default='А. Масалиева 44, ТЦ Корона, 3 этаж, Ош, Кыргызстан')
    instagram = models.URLField('Instagram', blank=True, default='https://www.instagram.com/edupoint.ec')
    telegram = models.URLField('Telegram', blank=True)
    youtube = models.URLField('YouTube', blank=True)
    tiktok = models.URLField('TikTok', blank=True)
    logo = models.ImageField('Логотип', upload_to='settings/', blank=True)
    favicon = models.ImageField('Favicon', upload_to='settings/', blank=True)
    meta_title = models.CharField('SEO: Title', max_length=255, default='Edu Point — Языковой центр в Оше')
    meta_description = models.TextField('SEO: Description', default='Изучайте корейский, английский, немецкий и китайский языки в Edu Point. Подготовка к TOPIK, IELTS, GOETHE. Ош, Кыргызстан.')

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def __str__(self):
        return 'Настройки сайта'

    def save(self, *args, **kwargs):
        # Singleton pattern — only one settings object
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class GalleryImage(models.Model):
    """Галерея фотографий учебного центра."""
    CATEGORY_CHOICES = [
        ('classes', 'Классы'),
        ('events', 'Мероприятия'),
        ('students', 'Студенты'),
        ('other', 'Другое'),
    ]
    title = models.CharField('Заголовок', max_length=200)
    image = models.ImageField('Изображение', upload_to='gallery/')
    category = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES, default='other')
    uploaded_at = models.DateTimeField('Дата загрузки', auto_now_add=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Фото галереи'
        verbose_name_plural = 'Галерея'
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    """Сообщения из формы обратной связи."""
    name = models.CharField('Имя', max_length=200)
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Телефон', max_length=50, blank=True)
    message = models.TextField('Сообщение')
    created_at = models.DateTimeField('Дата', auto_now_add=True)
    is_read = models.BooleanField('Прочитано', default=False)

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения с сайта'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.created_at.strftime("%d.%m.%Y")}'
