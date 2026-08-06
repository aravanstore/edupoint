import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Game, GameRoom, GameResult, RoomPlayer

AVATARS = ['😎', '🎓', '🦁', '🚀', '🦊', '🦉', '⭐', '🔥']

def index_view(request):
    """Games hub main page."""
    games = Game.objects.filter(is_active=True).order_by('order', 'id')
    categories = [
        ('all', '🌟 Все игры'),
        ('vocab', '🔤 Словарный запас'),
        ('mafia', '🕵️ Мафия и логика'),
        ('grammar', '✍️ Грамматика'),
        ('typing', '⚡ Скорость и память'),
        ('exam', '🏆 Экзамены и Дуэли'),
    ]
    context = {
        'games': games,
        'categories': categories,
        'page_title': 'Игровой Центр — Изучение языков в игре | Edu Point',
    }
    return render(request, 'games/index.html', context)


def room_select_view(request, slug):
    """Room selection (Rooms 1..4) for a chosen minigame."""
    game = get_object_or_404(Game, slug=slug, is_active=True)

    # Ensure 4 rooms exist for this game
    rooms = []
    for num in range(1, 5):
        room, created = GameRoom.objects.get_or_create(
            game=game,
            room_number=num,
            defaults={
                'name': f'Комната #{num}',
                'host_name': 'Свободна (нажмите стать хостом)',
                'difficulty': 'easy',
                'max_rounds': game.default_rounds,
                'round_time_sec': game.default_time_sec,
                'max_players': 4,
                'status': 'waiting'
            }
        )
        # Update is_occupied based on player count
        if room.players.count() == 0 and room.is_occupied:
            room.reset_room()
        rooms.append(room)

    if request.method == 'POST':
        room_num = int(request.POST.get('room_number', 1))
        room = get_object_or_404(GameRoom, game=game, room_number=room_num)

        player_name = request.POST.get('player_name', 'Игрок').strip() or 'Игрок'
        request.session['player_name'] = player_name

        if not request.session.session_key:
            request.session.save()

        session_key = request.session.session_key

        # If room is free/empty, claim host
        if not room.is_occupied or room.players.count() == 0:
            room.host_name = player_name
            room.host_session_id = session_key
            room.is_occupied = True
            room.status = 'waiting'

            # Apply custom host settings
            if 'difficulty' in request.POST:
                room.difficulty = request.POST.get('difficulty', 'easy')
            if 'max_rounds' in request.POST:
                room.max_rounds = int(request.POST.get('max_rounds', 10))
            if 'round_time_sec' in request.POST:
                room.round_time_sec = int(request.POST.get('round_time_sec', 20))
            if 'max_players' in request.POST:
                room.max_players = int(request.POST.get('max_players', 4))
            if 'target_language' in request.POST:
                room.target_language = request.POST.get('target_language', 'korean')

            room.save()

        # Add player to RoomPlayer DB model
        is_host = (room.host_session_id == session_key or room.host_name == player_name)
        RoomPlayer.objects.update_or_create(
            room=room,
            session_key=session_key,
            defaults={
                'player_name': player_name,
                'is_host': is_host,
                'is_ready': True,
                'avatar': random.choice(AVATARS),
                'last_seen': timezone.now()
            }
        )

        return redirect('games:play', slug=game.slug, room_number=room.room_number)

    from django.db.models import Count, Max
    top_results = (
        GameResult.objects.filter(game=game)
        .values('player_name')
        .annotate(
            wins_count=Count('id'),
            best_score=Max('score')
        )
        .order_by('-wins_count', '-best_score')[:5]
    )

    context = {
        'game': game,
        'rooms': rooms,
        'top_results': top_results,
        'page_title': f'Выбор комнаты — {game.title} | Edu Point',
    }
    return render(request, 'games/room_select.html', context)


def play_view(request, slug, room_number):
    """Main Game Arena view."""
    game = get_object_or_404(Game, slug=slug, is_active=True)
    room = get_object_or_404(GameRoom, game=game, room_number=room_number)

    player_name = request.session.get('player_name', 'Игрок')
    session_key = request.session.session_key

    is_host = False
    if session_key and room.host_session_id == session_key:
        is_host = True
    elif room.host_name == player_name:
        is_host = True

    # Register active player in RoomPlayer if not present
    if session_key:
        RoomPlayer.objects.update_or_create(
            room=room,
            session_key=session_key,
            defaults={
                'player_name': player_name,
                'is_host': is_host,
                'is_ready': True,
                'last_seen': timezone.now()
            }
        )

    top_leaderboard = GameResult.objects.filter(game=game).order_by('-score')[:5]

    context = {
        'game': game,
        'room': room,
        'player_name': player_name,
        'is_host': is_host,
        'top_leaderboard': top_leaderboard,
        'page_title': f'{game.icon} {game.title} — Комната #{room.room_number} | Edu Point',
    }
    return render(request, 'games/play.html', context)


def room_status_api(request, slug, room_number):
    """Returns real-time connected players list and room status for lobby polling."""
    game = get_object_or_404(Game, slug=slug)
    room = get_object_or_404(GameRoom, game=game, room_number=room_number)

    session_key = request.session.session_key
    player_name = request.session.get('player_name', 'Игрок')

    # Update last_seen for current player
    if session_key:
        RoomPlayer.objects.filter(room=room, session_key=session_key).update(last_seen=timezone.now())

    # Get list of REAL connected players
    active_players = RoomPlayer.objects.filter(room=room).order_by('joined_at')
    players_data = [
        {
            'name': p.player_name,
            'is_host': p.is_host,
            'is_ready': p.is_ready,
            'avatar': p.avatar
        }
        for p in active_players
    ]

    is_current_host = False
    if session_key and room.host_session_id == session_key:
        is_current_host = True
    elif room.host_name and player_name and room.host_name.strip() == player_name.strip():
        is_current_host = True
    elif active_players.count() <= 1:
        # Single player in room is always Host!
        is_current_host = True
        if session_key:
            room.host_session_id = session_key
            room.host_name = player_name
            room.save(update_fields=['host_session_id', 'host_name'])
            RoomPlayer.objects.filter(room=room, session_key=session_key).update(is_host=True)

    return JsonResponse({
        'status': room.status,
        'is_occupied': room.is_occupied,
        'host_name': room.host_name,
        'is_host': is_current_host,
        'max_players': room.max_players,
        'max_rounds': room.max_rounds,
        'round_time_sec': room.round_time_sec,
        'target_language': room.target_language,
        'difficulty': room.difficulty,
        'players': players_data
    })


@csrf_exempt
def start_game_api(request, slug, room_number):
    """Host launches game for all players in room."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    game = get_object_or_404(Game, slug=slug)
    room = get_object_or_404(GameRoom, game=game, room_number=room_number)

    room.status = 'in_game'
    room.is_occupied = True
    room.save()

    return JsonResponse({'success': True, 'status': 'in_game'})


@csrf_exempt
def reset_room_api(request, slug, room_number):
    """Resets room status back to free when game ends or host exits."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    game = get_object_or_404(Game, slug=slug)
    room = get_object_or_404(GameRoom, game=game, room_number=room_number)

    room.reset_room()

    return JsonResponse({'success': True, 'message': 'Комната снова свободна!'})


@csrf_exempt
def save_result_api(request, slug):
    """API endpoint to record game result and get current podium."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        game = get_object_or_404(Game, slug=slug)

        player_name = data.get('player_name', 'Игрок')
        score = int(data.get('score', 0))
        correct = int(data.get('correct_answers', 0))
        total = int(data.get('total_answers', 0))
        room_num = int(data.get('room_number', 1))

        # Check if score is top score in this room/match
        is_winner = (score > 0 and correct > 0)

        result = GameResult.objects.create(
            game=game,
            room_number=room_num,
            player_name=player_name,
            score=score,
            correct_answers=correct,
            total_answers=total,
            is_win=is_winner
        )

        # Reset room to free status after game finishes
        try:
            room = GameRoom.objects.get(game=game, room_number=room_num)
            room.reset_room()
        except GameRoom.DoesNotExist:
            pass

        top_3 = GameResult.objects.filter(game=game).order_by('-score')[:3]
        podium = [
            {'name': r.player_name, 'score': r.score, 'correct': r.correct_answers}
            for r in top_3
        ]

        return JsonResponse({
            'success': True,
            'player_score': score,
            'podium': podium
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def leaderboard_api(request, slug):
    """Returns top players sorted by total Victories (🏆 Победы)."""
    game = get_object_or_404(Game, slug=slug)
    from django.db.models import Count, Max

    leaderboard_qs = (
        GameResult.objects.filter(game=game)
        .values('player_name')
        .annotate(
            wins_count=Count('id'),
            best_score=Max('score')
        )
        .order_by('-wins_count', '-best_score')[:10]
    )

    data = [
        {
            'name': item['player_name'],
            'wins': item['wins_count'],
            'best_score': item['best_score']
        }
        for item in leaderboard_qs
    ]
    return JsonResponse({'game': game.title, 'leaderboard': data})
