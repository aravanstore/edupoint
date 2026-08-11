from django.urls import path
from . import views, crm_views, analytics_views

app_name = 'applications'

urlpatterns = [
    # Публичная форма записи
    path('', views.apply, name='apply'),

    # ---- CRM: наборы групп ----
    path('crm/sets/', crm_views.set_list, name='set_list'),
    path('crm/sets/create/', crm_views.set_create, name='set_create'),
    path('crm/sets/<int:pk>/', crm_views.set_detail, name='set_detail'),
    path('crm/sets/<int:pk>/edit/', crm_views.set_edit, name='set_edit'),
    path('crm/sets/<int:pk>/status/', crm_views.set_status, name='set_status'),
    path('crm/sets/<int:pk>/create-group/', crm_views.set_create_group, name='set_create_group'),

    # ---- CRM: заявки (воронка) ----
    path('crm/applications/', crm_views.application_list, name='application_list'),
    path('crm/applications/create/', crm_views.application_create, name='application_create'),
    path('crm/applications/<int:pk>/', crm_views.application_detail, name='application_detail'),
    path('crm/applications/<int:pk>/status/', crm_views.application_status, name='application_status'),
    path('crm/applications/<int:pk>/notes/', crm_views.application_notes, name='application_notes'),

    # ---- CRM: лист ожидания ----
    path('crm/waitlist/', crm_views.waitlist_list, name='waitlist_list'),
    path('crm/waitlist/<int:set_pk>/add/', crm_views.waitlist_add, name='waitlist_add'),
    path('crm/waitlist/<int:pk>/notify/', crm_views.waitlist_mark_notified, name='waitlist_notify'),

    # ---- Аналитика ----
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    path('analytics/courses/', analytics_views.analytics_courses, name='analytics_courses'),
    path('analytics/teachers/', analytics_views.analytics_teachers, name='analytics_teachers'),
    path('analytics/attendance/', analytics_views.analytics_attendance, name='analytics_attendance'),
    path('analytics/financial/', analytics_views.analytics_financial, name='analytics_financial'),
    path('analytics/marketing/', analytics_views.analytics_marketing, name='analytics_marketing'),
    path('analytics/export/', analytics_views.export_view, name='analytics_export'),
]
