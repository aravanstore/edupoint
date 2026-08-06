from django.urls import path
from . import views

app_name = 'games'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('<slug:slug>/rooms/', views.room_select_view, name='room_select'),
    path('<slug:slug>/room/<int:room_number>/', views.play_view, name='play'),
    path('<slug:slug>/room/<int:room_number>/status/', views.room_status_api, name='room_status_api'),
    path('<slug:slug>/room/<int:room_number>/start/', views.start_game_api, name='start_game_api'),
    path('<slug:slug>/room/<int:room_number>/reset/', views.reset_room_api, name='reset_room_api'),
    path('api/<slug:slug>/save-result/', views.save_result_api, name='save_result_api'),
    path('api/<slug:slug>/leaderboard/', views.leaderboard_api, name='leaderboard_api'),
]
