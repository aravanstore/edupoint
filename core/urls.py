from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('gallery/', views.gallery, name='gallery'),
    path('contact/', views.contact, name='contact'),
    path('search/', views.search, name='search'),
    path('egg/<slug:egg_id>/', views.egg_found, name='egg_found'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]
