from django.db import models
from django.utils.text import slugify
from ckeditor.fields import RichTextField


class NewsPost(models.Model):
    """Новости учебного центра."""
    title = models.CharField('Заголовок', max_length=300)
    slug = models.SlugField('URL', unique=True, blank=True)
    excerpt = models.TextField('Краткое описание', max_length=300, blank=True)
    content = RichTextField('Содержание')
    image = models.ImageField('Изображение', upload_to='news/', blank=True)
    is_published = models.BooleanField('Опубликовано', default=True)
    published_at = models.DateTimeField('Дата публикации', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    views = models.PositiveIntegerField('Просмотры', default=0)

    # SEO
    meta_title = models.CharField('SEO: Title', max_length=255, blank=True)
    meta_description = models.TextField('SEO: Description', blank=True)

    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('news:detail', kwargs={'slug': self.slug})


class BlogPost(models.Model):
    """Статьи блога об изучении языков."""
    CATEGORY_CHOICES = [
        ('korean', 'Корейский язык'),
        ('english', 'Английский язык'),
        ('german', 'Немецкий язык'),
        ('chinese', 'Китайский язык'),
        ('tips', 'Советы по обучению'),
        ('exams', 'Экзамены'),
        ('study_abroad', 'Учёба за рубежом'),
        ('other', 'Другое'),
    ]
    title = models.CharField('Заголовок', max_length=300)
    slug = models.SlugField('URL', unique=True, blank=True)
    category = models.CharField('Категория', max_length=20, choices=CATEGORY_CHOICES, default='other')
    excerpt = models.TextField('Краткое описание', max_length=300, blank=True)
    content = RichTextField('Содержание')
    image = models.ImageField('Изображение', upload_to='blog/', blank=True)
    tags = models.CharField('Теги', max_length=300, blank=True, help_text='Через запятую')
    is_published = models.BooleanField('Опубликовано', default=True)
    published_at = models.DateTimeField('Дата публикации', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    views = models.PositiveIntegerField('Просмотры', default=0)

    # SEO
    meta_title = models.CharField('SEO: Title', max_length=255, blank=True)
    meta_description = models.TextField('SEO: Description', blank=True)

    class Meta:
        verbose_name = 'Статья блога'
        verbose_name_plural = 'Блог'
        ordering = ['-published_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('blog:detail', kwargs={'slug': self.slug})

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
