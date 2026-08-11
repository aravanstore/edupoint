from django import forms
from django.utils import timezone

from .models import GroupSet, StudentApplication, WaitlistEntry, DAYS


class GroupSetForm(forms.ModelForm):
    days = forms.MultipleChoiceField(
        label='Дни занятий',
        choices=DAYS,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-inline'}),
    )

    class Meta:
        model = GroupSet
        fields = ['name', 'course', 'teacher', 'days', 'start_time', 'end_time',
                  'start_date', 'capacity', 'branch', 'status', 'is_night']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control',
                                           'placeholder': 'Пусто — сгенерируется автоматически'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'is_night': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].required = False
        self.fields['branch'].required = False
        self.fields['capacity'].required = False
        self.fields['start_date'].required = False
        self.fields['name'].required = False
        if self.instance and self.instance.pk and self.instance.days:
            self.initial['days'] = self.instance.days_codes()

    def clean_days(self):
        codes = self.cleaned_data.get('days') or []
        return ','.join(codes)


class WaitlistForm(forms.ModelForm):
    class Meta:
        model = WaitlistEntry
        fields = ['name', 'phone', 'note']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+996 ...'}),
            'note': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Примечание (необязательно)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['note'].required = False


class ApplicationNoteForm(forms.ModelForm):
    class Meta:
        model = StudentApplication
        fields = ['notes']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                           'placeholder': 'Внутренние заметки CRM...'}),
        }
        labels = {'notes': 'Заметки CRM'}


class ApplicationStatusForm(forms.Form):
    status = forms.ChoiceField(
        label='Новый статус',
        choices=StudentApplication.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    note = forms.CharField(
        label='Примечание (необязательно)',
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: договорились о тесте'}),
    )
