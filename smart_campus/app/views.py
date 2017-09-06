from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import auth
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

import os

from .models import (
    User, Reward, Permission,
    Station, StationCategory,
    Beacon, StationImage,
)
from .forms import StationForm


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
        return JsonResponse({'status': 'true', 'message': 'Success', 'data': user_data}, json_dumps_params={'ensure_ascii': False}, content_type='application/json; charset=utf-8')

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
    """Show all stations managed by the user's group"""
    if request.user.can(Permission.ADMIN):
        stations = Station.objects.all()
    else:
        stations = Station.objects.filter(owner_group=request.user.group)

    station_data = [
        {
            'id': station.id,
            'name': station.name,
            'image_url': station.primary_image_url,
        }
        for station in stations
    ]

    context = {'email': request.user.email, 'stations': station_data}

    return render(request, 'app/station_list.html', context)


@login_required
def station_edit_page(request, pk):
    station = get_object_or_404(Station, pk=pk)

    if (not station.owner_group == request.user.group and
            not request.user.is_administrator()):
        return HttpResponseForbidden()

    if request.method == 'POST':
        # Delete Station request
        if request.POST.get('delete_confirmed') == 'true':
            station.delete()
            return HttpResponseRedirect('/stations/')

        # Use custom StationForm to validate form datas
        # is_valid() will be true if received data is good
        # There'll be error messages in 'form' instance if validation failed
        # cleaned_data will be the form inputs from the request
        form = StationForm(request.POST, request.FILES, instance=station)
        if form.is_valid():
            data = form.cleaned_data
            station = form.save(commit=False)
            station.location = Point(x=data['lng'], y=data['lat'])

            # Clear linked Beacons
            station.beacon_set.clear()
            station.beacon_set.add(Beacon.objects.get(name=data['beacon']))
            station.save()

            # Handle change of images
            if request.POST.get('img_changed') == 'true':
                # Clear old images
                for img in StationImage.objects.filter(station=station):
                    # Clear files on the disk
                    # Delete model instance won't delete them
                    if os.path.isfile(img.image.path):
                        os.remove(img.image.path)
                    img.delete()

                # Add new images
                for key, value in data.items():
                    if isinstance(value, InMemoryUploadedFile):
                        is_primary = (key == 'img{0}'.format(data['main_img_num']))
                        StationImage.objects.create(
                            station=station,
                            image=value,
                            is_primary=is_primary
                        )

            return HttpResponseRedirect('/stations/')

        # if the datas failed in validation
        # save the inputs back for redirection
        form_data = form.cleaned_data
    else:
        form = StationForm()

        # Load datas from the model instance
        form_data = {
            'name': station.name,
            'category': station.category,
            'content': station.content,
            'beacon': station.beacon_set.first().name,
            'lng': station.location.x,
            'lat': station.location.y
        }

    if request.user.can(Permission.ADMIN):
        beacon_set = Beacon.objects.all()
    elif request.user.can(Permission.EDIT):
        beacon_set = Beacon.objects.filter(owner_group=request.user.group)
    else:
        return HttpResponseForbidden()

    context = {
        'email': request.user.email,
        'categories': StationCategory.objects.all(),
        'beacons': beacon_set,
        'form': form,
        'form_data': form_data,
        'max_imgs': settings.MAX_IMGS_UPLOAD,
    }
    return render(request, 'app/station_edit.html', context)


@login_required
def station_new_page(request):
    if request.method == 'POST':
        # Use custom StationForm to validate form datas
        # is_valid() will be true if received data is good
        # There'll be error messages in 'form' instance if validation failed
        # cleaned_data will be the form inputs from the request
        form = StationForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            station = form.save(commit=False)
            station.location = Point(x=data['lng'], y=data['lat'])
            station.owner_group = request.user.group
            station.save()
            # save first
            # need an instance to add beacons
            station.beacon_set.add(Beacon.objects.get(name=data['beacon']))
            station.save()
 
            # Add images
            for key, value in data.items():
                if isinstance(value, InMemoryUploadedFile):
                    is_primary = (key == 'img{0}'.format(data['main_img_num']))
                    StationImage.objects.create(
                        station=station,
                        image=value,
                        is_primary=is_primary
                    )

            return HttpResponseRedirect('/stations/')
    else:
        form = StationForm()

    if request.user.can(Permission.ADMIN):
        beacon_set = Beacon.objects.all()
    elif request.user.can(Permission.EDIT):
        beacon_set = Beacon.objects.filter(owner_group=request.user.group)
    else:
        return HttpResponseForbidden()

    context = {
        'email': request.user.email,
        'categories': StationCategory.objects.all(),
        'beacons': beacon_set,
        'form': form,
        'max_imgs': settings.MAX_IMGS_UPLOAD,
    }
    return render(request, 'app/station_new.html', context)


@csrf_exempt
def get_all_rewards(request):
    """API for retrieving rewards list"""
    data = [{'id': reward.id, 'name': reward.name, 'image_url': 'http://{0}/{1}'.format(request.get_host(), reward.image.url)}
            for reward in Reward.objects.all()]

    return JsonResponse({'status': 'true', 'message': 'Success', 'data': data}, json_dumps_params={'ensure_ascii': False}, content_type='application/json; charset=utf-8')


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
            'image': [{'image_url': 'http://{0}/{1}'.format(request.get_host(), img.image.url), 'primary': img.is_primary}
                      for img in station.stationimage_set.all()]
        }
        for station in Station.objects.all()
    ]

    return JsonResponse({'status': 'true', 'message': 'Success', 'data': data}, json_dumps_params={'ensure_ascii': False}, content_type='application/json; charset=utf-8')
