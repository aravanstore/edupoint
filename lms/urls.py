from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'lms'

urlpatterns = [
    # Аутентификация
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html',
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html',
    ), name='password_reset_complete'),

    # Общие
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('notifications/', views.notifications_view, name='notifications'),

    # Админ / аналитика / история
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('admin/activity/', views.activity_log_view, name='activity_log'),

    # Ученик
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/grades/', views.student_grades, name='student_grades'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/homework/', views.student_homework, name='student_homework'),
    path('student/homework/<int:pk>/submit/', views.student_homework_submit, name='student_homework_submit'),
    path('student/schedule/', views.student_schedule, name='student_schedule'),
    path('student/announcements/', views.student_announcements, name='student_announcements'),

    # Родитель
    path('parent/', views.parent_dashboard, name='parent_dashboard'),

    # Учитель
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/journal/<int:group_pk>/', views.teacher_journal, name='teacher_journal'),
    path('teacher/homework/', views.teacher_homework, name='teacher_homework'),
    path('teacher/announcements/', views.teacher_announcements, name='teacher_announcements'),

    # Ресепшен
    path('reception/', views.reception_dashboard, name='reception_dashboard'),
    path('reception/groups/', views.reception_groups, name='reception_groups'),
    path('reception/groups/<int:pk>/', views.reception_group_detail, name='reception_group_detail'),
    path('reception/teachers/add/', views.reception_teacher_add, name='reception_teacher_add'),
    path('reception/students/', views.reception_students, name='reception_students'),
    path('reception/students/add/', views.reception_student_add, name='reception_student_add'),
    path('reception/students/<int:pk>/', views.reception_student_detail, name='reception_student_detail'),
    path('reception/announcements/', views.reception_announcements, name='reception_announcements'),
]
