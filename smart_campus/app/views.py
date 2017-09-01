from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import auth
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import (
    User, Reward, Permission,
    Station, StationCategory
)


@csrf_exempt
@require_POST
def signup(request):
    """Signup API for APP users

    Register new users

    """
    email = request.POST.get('email')
    password = request.POST.get('password')
    nickname = request.POST.get('nickname')

    if User.objects.filter(email=email).exists():
        return JsonResponse({'status': 'false', 'message': 'User already exists!'})

    try:
        User.objects.create_user(email, password, nickname)
    except ValueError as error:
        return JsonResponse({'status': 'false', 'message': error})

    return JsonResponse({'status': 'true', 'message': 'Success'})


@csrf_exempt
@require_POST
def login(request):
    """Login API for APP users

    Handle login requests from app

    """
    email = request.POST.get('email')
    password = request.POST.get('password')
    user = auth.authenticate(request, username=email, password=password)
    if user is not None:
        auth.login(request, user)
        user_data = {
            'nickname': user.nickname,
            'experience_point': user.experience_point,
            'coins': user.earned_coins,
            'reward': [reward.id for reward in user.received_rewards.all()],
            'favorite_stations': [station.id for station in user.favorite_stations.all()],
        }
        return JsonResponse({'status': 'true', 'message': 'Success', 'data': user_data})

    return JsonResponse({'status': 'false', 'message': 'Login failed'})


@csrf_exempt
@require_POST
def logout(request):
    """Logout API for APP users

    Handle logout requests from app

    """
    auth.logout(request)
    return JsonResponse({'status': 'true', 'message': 'Success'})


@csrf_exempt
def login_page(request):
    """Login for Management Backend Page

    Render Login page and handle login requests for the Management backend

    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = auth.authenticate(request, username=email, password=password)

        if not user:
            messages.warning(request, 'Login failed!')
            return HttpResponseRedirect('/login/')

        if user.can(Permission.EDIT) or user.can(Permission.ADMIN):
            auth.login(request, user)
            return HttpResponseRedirect('/')

    else:
        if request.user.is_authenticated():
            return HttpResponseRedirect('/')

    return render(request, 'app/login.html')


@login_required
def logout_page(request):
    auth.logout(request)
    return HttpResponseRedirect('/login/')


@login_required
def index(request):
    context = {'email': request.user.email}
    return render(request, 'app/index.html', context)


@login_required
def station_list_page(request):
    context = {'email': request.user.email}
    return render(request, 'app/station_list.html', context)


@login_required
def add_station_page(request):
    context = {'email': request.user.email, 'categories': StationCategory.objects.all()}
    return render(request, 'app/add_station.html', context)


@csrf_exempt
def get_all_rewards(request):
    """API for retrieving rewards list"""
    data = [{'id': reward.id, 'name': reward.name, 'image_url': reward.image.url}
            for reward in Reward.objects.all()]

    return JsonResponse({'status': 'true', 'message': 'Success', 'data': data})


@csrf_exempt
def get_all_stations(request):
    """API for retrieving contents of all Stations"""
    data = [
        {
            'id': station.id,
            'name': station.name,
            'content': station.content,
            'category': str(station.category),
            'location': station.location.get_coords(),
            'image': [{'image_url': img.image.url, 'primary': img.is_primary}
                      for img in station.stationimage_set.all()]
        }
        for station in Station.objects.all()
    ]

    return JsonResponse({'status': 'true', 'message': 'Success', 'data': data})
