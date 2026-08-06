from django.db import models
from ckeditor.fields import RichTextField


class Exam(models.Model):
    """Международные экзамены (TOPIK, IELTS, GOETHE)."""
    EXAM_CHOICES = [
        ('topik', 'TOPIK'),
        ('ielts', 'IELTS'),
        ('goethe', 'GOETHE'),
    ]
    name = models.CharField('Название', max_length=10, choices=EXAM_CHOICES, unique=True)
    full_name = models.CharField('Полное название', max_length=200, blank=True)
    description = RichTextField('Описание экзамена')
    preparation_program = RichTextField('Программа подготовки', blank=True)
    benefits = models.TextField('Преимущества курса', blank=True, help_text='Каждое с новой строки')
    image = models.ImageField('Изображение', upload_to='exams/', blank=True)
    duration = models.CharField('Длительность подготовки', max_length=100, blank=True)
    price = models.DecimalField('Цена (сом)', max_digits=8, decimal_places=0, default=0)
    is_active = models.BooleanField('Активен', default=True)
    order = models.PositiveIntegerField('Порядок', default=0)

    # SEO
    meta_title = models.CharField('SEO: Title', max_length=255, blank=True)
    meta_description = models.TextField('SEO: Description', blank=True)

    class Meta:
        verbose_name = 'Экзамен'
        verbose_name_plural = 'Экзамены'
        ordering = ['order']

    def __str__(self):
        return self.get_name_display()

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('exams:detail', kwargs={'name': self.name})

    def get_benefits_list(self):
        return [b.strip() for b in self.benefits.split('\n') if b.strip()]
