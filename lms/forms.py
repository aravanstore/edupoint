from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from teachers.models import Teacher


class TeacherForm(forms.ModelForm):
    password = forms.CharField(label='Пароль для входа в кабинет', max_length=128, required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'placeholder': 'Если пусто — будет сгенерирован'}))

    class Meta:
        model = Teacher
        fields = ['name', 'position', 'photo', 'bio', 'experience_years', 'education',
                  'languages', 'instagram', 'telegram', 'is_active', 'profile_theme']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'education': forms.TextInput(attrs={'class': 'form-control'}),
            'languages': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Корейский, английский'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'profile_theme': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in ('bio', 'education', 'instagram', 'telegram', 'photo', 'profile_theme'):
            self.fields[f].required = False

from .models import (
    Group, Homework, HomeworkSubmission, Payment, PaymentExtension,
    Announcement, StudentProfile, Grade, Attendance,
)


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваш логин', 'autofocus': True}),
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ваш пароль'}),
    )
    remember = forms.BooleanField(
        label='Запомнить меня на 30 дней',
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )


class StudentForm(forms.ModelForm):
    first_name = forms.CharField(label='Имя', max_length=150,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Фамилия', max_length=150, required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', max_length=128, required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control',
                                                             'help_text': 'Если пусто — будет сгенерирован'}))
    group_set = forms.ModelChoiceField(
        label='Или открытый набор', queryset=None, required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Если группы для этого набора ещё нет — она будет создана автоматически'
    )

    class Meta:
        model = StudentProfile
        fields = ['group', 'book', 'book_progress', 'parent', 'phone', 'parent_phone',
                  'birth_date', 'trial_date', 'notes', 'is_active']
        widgets = {
            'group': forms.Select(attrs={'class': 'form-select'}),
            'book': forms.Select(attrs={'class': 'form-select'}),
            'book_progress': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+996 ...'}),
            'parent_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+996 ... (необязательно)'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'trial_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from applications.models import GroupSet
        self.fields['group_set'].queryset = GroupSet.objects.filter(status='open').select_related('course', 'teacher')
        self.fields['group'].required = False
        self.fields['parent'].required = False
        self.fields['book'].required = False
        self.fields['phone'].required = False
        self.fields['parent_phone'].required = False
        self.fields['birth_date'].required = False
        self.fields['trial_date'].required = False
        self.fields['notes'].required = False

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('group') and not cleaned.get('group_set'):
            raise forms.ValidationError('Выберите группу или открытый набор — одно из двух обязательно.')
        return cleaned


class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ['group', 'title', 'description', 'photo', 'video', 'file', 'due_date']
        widgets = {
            'group': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Изучить грамматику, урок 5'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                                 'placeholder': 'Текст задания...'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'video': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/...'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = False
        self.fields['video'].required = False
        self.fields['file'].required = False
        self.fields['due_date'].required = False


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['text', 'photo']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                          'placeholder': 'Ваш ответ...'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['photo'].required = False


class PaymentForm(forms.ModelForm):
    month = forms.DateField(
        label='Месяц оплаты', initial=timezone.localdate().replace(day=1),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    class Meta:
        model = Payment
        fields = ['month', 'amount', 'method', 'is_confirmed', 'note']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'method': forms.Select(attrs={'class': 'form-select'}),
            'is_confirmed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'note': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Примечание (необязательно)'}),
        }


class ExtensionForm(forms.ModelForm):
    month = forms.DateField(
        label='Месяц', initial=timezone.localdate().replace(day=1),
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
    )

    class Meta:
        model = PaymentExtension
        fields = ['month', 'new_due_date', 'reason']
        widgets = {
            'new_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Причина отсрочки'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reason'].required = False


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['group', 'title', 'text']
        widgets = {
            'group': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control',
                                           'placeholder': 'Например: Завтра занятия отменяются'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4,
                                          'placeholder': 'Текст объявления...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['group'].required = False


class GradeAttendanceForm(forms.Form):
    """Форма одной строки журнала: оценка + посещение для ученика."""

    def __init__(self, *args, students=None, date=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.students = students or []
        self.date = date
        for student in self.students:
            grade = student.grades.filter(date=date).first()
            att = student.attendance_records.filter(date=date).first()
            self.fields[f'grade_{student.id}'] = forms.IntegerField(
                required=False, min_value=0, max_value=10, initial=grade.value if grade else None,
                widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm text-center',
                                                'style': 'max-width:70px;', 'min': 0, 'max': 10}))
            self.fields[f'att_{student.id}'] = forms.ChoiceField(
                required=False,
                choices=[('', '—')] + Attendance.STATUS_CHOICES,
                initial=att.status if att else '',
                widget=forms.Select(attrs={'class': 'form-select form-select-sm',
                                           'style': 'max-width:150px;'}))
            self.fields[f'comment_{student.id}'] = forms.CharField(
                required=False, max_length=300, initial=grade.comment if grade else '',
                widget=forms.TextInput(attrs={'class': 'form-control form-control-sm',
                                              'placeholder': 'Комментарий'}))

    def save(self, teacher, group):
        created_grades = created_att = 0
        for student in self.students:
            grade_val = self.cleaned_data.get(f'grade_{student.id}')
            att_val = self.cleaned_data.get(f'att_{student.id}')
            comment = self.cleaned_data.get(f'comment_{student.id}', '')

            if grade_val is not None:
                Grade.objects.update_or_create(
                    student=student, date=self.date,
                    defaults={'value': grade_val, 'comment': comment,
                              'group': group, 'teacher': teacher},
                )
                created_grades += 1

            if att_val:
                Attendance.objects.update_or_create(
                    student=student, date=self.date,
                    defaults={'status': att_val, 'group': group},
                )
                created_att += 1
        return created_grades, created_att


class ProfileForm(forms.Form):
    first_name = forms.CharField(label='Имя', max_length=150,
                                 widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Фамилия', max_length=150, required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Email', required=False,
                             widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label='Телефон', max_length=50, required=False,
                            widget=forms.TextInput(attrs={'class': 'form-control'}))
