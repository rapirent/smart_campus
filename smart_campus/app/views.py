from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET, require_safe
from django.contrib import auth
from django.http import (
    HttpResponseRedirect,
    JsonResponse,
    HttpResponseForbidden,
    HttpResponse
)
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.gis.geos import Point
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.core import serializers
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.tokens import default_token_generator

import os
import random
import json
from functools import wraps
import pytz

from .models import (
    User, Reward, Permission,
    Station, StationCategory,
    Beacon, StationImage, Question,
    UserReward, UserGroup,
    TravelPlan, Role,
    TravelPlanStations,
    Choice, UserVisitedBeacons
)
from .forms import (
    PartialStationForm,
    StationCategoryForm,
    ManagerForm,
    PartialRewardForm,
    PartialTravelPlanForm,
    RewardForm,
    BeaconForm,
    QuestionForm,
    PartialManagerForm
)
from .tokens import account_activation_token


def administrator_required(function):
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_administrator():
            return HttpResponseForbidden()
        return function(request, *args, **kwargs)
    return wrapper


def activate_required(function):
    @wraps(function)
    def wrapper(request, email, *args, **kargs):
        try:
            request.user = User.objects.get(email=email)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return HttpResponse('The user does not exist.', status=400)
        if not request.user.email_confirmed:
            return HttpResponse('The user is not activated.', status=401)
        return function(request, email, *args, **kargs)
    return wrapper


@csrf_exempt
@require_POST
def signup(request):
    """Signup API for APP users

    Register new users

    """
    user_email = request.POST.get('email')
    password = request.POST.get('password')
    nickname = request.POST.get('nickname')

    if not user_email or not password or not nickname:
        return HttpResponse('Either email, password or nickname input is missing.', status=422)
    
    user_email = User.objects.normalize_email(user_email)

    if User.objects.filter(email=user_email).exists():
        return HttpResponse('The email is already taken, try another!', status=409)

    try:
        user = User.objects.create_user(user_email, password, nickname)
    except (ValueError, ValidationError) as error:
        return HttpResponse(error, status=400)
    except IntegrityError:
        return HttpResponse('The email is already taken, try another!', status=409)

    message = render_to_string('email/activation.html', {
        'prefix': 'https://' if request.is_secure() else 'http://',
        'user': user,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'expired_days': settings.PASSWORD_RESET_TIMEOUT_DAYS
    })
    mail_subject = '[NCKU Smart Campus App] Please activate your account'
    email = EmailMessage(mail_subject, message, to=[user_email])
    email.send()

    return HttpResponse('Registration succeeded!', status=201)


@csrf_exempt
@require_POST
def login(request):
    """Login API for APP users

    Handle login requests from app

    """
    user_email = request.POST.get('email')
    password = request.POST.get('password')
    user = auth.authenticate(request, username=user_email, password=password)

    if user is not None:
        auth.login(request, user)
        user_data = {
            'nickname': user.nickname,
            'experience_point': user.experience_point,
            'coins': user.earned_coins,
            'rewards': [
                user_reward.reward.id
                for user_reward in UserReward.objects.filter(user=user).order_by('timestamp')
            ],
            'favorite_stations': [
                station.id
                for station in user.favorite_stations.all()
            ],
        }
        return JsonResponse(
            data={
                'message': 'Login succeeded',
                'data': user_data
            },
            status=200,
            json_dumps_params={'ensure_ascii': False},
            content_type='application/json; charset=utf-8'
        )

    return HttpResponse('Login failed', status=401)


@csrf_exempt
@require_POST
def logout(request):
    """Logout API for APP users

    Handle logout requests from app

    """
    user_email = request.POST.get('email')
    request.user = User.objects.filter(email=user_email).first()

    if not request.user:
        return HttpResponse('User does not exist', status=404)

    auth.logout(request)
    return HttpResponse('Logout succeeded', status=200)


@csrf_exempt
def login_page(request):
    """Login for Management Backend Page

    Render Login page and handle login requests for the Management backend

    """
    if request.method == 'POST':
        user_email = request.POST.get('email')
        password = request.POST.get('password')
        user = auth.authenticate(request, username=user_email, password=password)

        if not user:
            messages.warning(request, 'Login failed!')
            return render(request, 'app/login.html')

        if user.can(Permission.EDIT) or user.can(Permission.ADMIN):
            auth.login(request, user)
            return HttpResponseRedirect('/')
        else:
            messages.warning(request, 'Login failed!')
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
    categories = StationCategory.objects.all().order_by('id')

    context = {
        'categories': categories,
    }
    return render(request, 'app/index.html', context)


@login_required
@csrf_exempt
def station_list_page(request):
    if request.user.can(Permission.ADMIN):
        station_list = Station.objects.all().order_by('id')
    else:
        station_list = Station.objects.filter(
            owner_group=request.user.group
        ).order_by('id')

    paginator = Paginator(station_list, 10)

    page = request.GET.get('page', 1)
    try:
        stations = paginator.page(page)
    except PageNotAnInteger:
        stations = paginator.page(1)
    except EmptyPage:
        stations = paginator.page(paginator.num_pages)

    for station in stations:
        station.primary_image = StationImage.objects.filter(
            station=station,
            is_primary=True
        ).first()
        station.beacon = Beacon.objects.filter(
            station=station
        ).first()

    context = {
        'stations': stations,
        'categories': StationCategory.objects.all().order_by('id')
    }

    return render(request, 'app/station_list_page.html', context)


@login_required
def station_list_by_category_page(request, pk):
    category = get_object_or_404(StationCategory, pk=pk)
    if request.user.can(Permission.ADMIN):
        station_list = Station.objects.filter(category=category).order_by('id')
    else:
        station_list = Station.objects.filter(owner_group=request.user.group, category=category).order_by('id')

    paginator = Paginator(station_list, 10)

    page = request.GET.get('page', 1)

    try:
        stations = paginator.page(page)
    except PageNotAnInteger:
        stations = paginator.page(1)
    except EmptyPage:
        stations = paginator.page(paginator.num_pages)

    for station in stations:
        station.primary_image = StationImage.objects.filter(
            station=station,
            is_primary=True
        ).first()
        station.beacon = Beacon.objects.filter(
            station=station
        ).first()

    context = {
        'stations': stations,
        'categories': StationCategory.objects.all().order_by('id')
    }

    return render(request, 'app/station_list_page.html', context)


@login_required
def station_edit_page(request, pk):
    station = get_object_or_404(Station, pk=pk)

    if (not station.owner_group == request.user.group and
            not request.user.is_administrator()):
        return HttpResponseForbidden()

    if request.method == 'POST':
        # Use custom PartialStationForm to validate form datas
        # is_valid() will be true if received data is good
        # There'll be error messages in 'form' instance if validation failed
        # cleaned_data will be the form inputs from the request
        form = PartialStationForm(request.POST, request.FILES, instance=station)
        if form.is_valid():
            data = form.cleaned_data
            station = form.save(commit=False)
            station.location = Point(x=data['lng'], y=data['lat'])

            # Clear linked Beacons
            station.beacon_set.clear()
            station.beacon_set.add(Beacon.objects.get(name=data['beacon']))
            station.save()

            # Add new images
            for key, value in data.items():
                if isinstance(value, UploadedFile):
                    StationImage.objects.create(
                        station=station,
                        image=value,
                        is_primary=False
                    )

            # link the reward related to the station
            station.reward_set.clear()
            reward = Reward.objects.filter(id=request.POST.get('reward', -1)).first()
            if reward:
                station.reward_set.add(reward)

            return HttpResponseRedirect('/stations/')

        # if the datas failed in validation
        # save the inputs back for redirection
        form_data = form.cleaned_data
    else:
        form = PartialStationForm()

        # Load datas from the model instance
        form_data = {
            'name': station.name,
            'category': station.category,
            'content': station.content,
            'beacon': station.beacon_set.first().name,
            'lng': station.location.x,
            'lat': station.location.y,
            'reward': station.reward_set.first(),
            'owner_group': station.owner_group,
        }

    if request.user.can(Permission.ADMIN):
        beacon_set = Beacon.objects.all()
        user_groups = UserGroup.objects.all().order_by('id')
    elif request.user.can(Permission.EDIT):
        beacon_set = Beacon.objects.filter(owner_group=request.user.group)
        user_groups = UserGroup.objects.filter(name=request.user.group)
    else:
        return HttpResponseForbidden()

    context = {
        'categories': StationCategory.objects.all().order_by('id'),
        'beacons': beacon_set,
        'form': form,
        'form_data': form_data,
        'max_imgs': settings.MAX_IMGS_UPLOAD,
        'images': StationImage.objects.filter(station_id=station.id),
        'rewards': Reward.objects.filter(related_station=None).union(station.reward_set.all()),
        'user_groups': user_groups,
    }
    return render(request, 'app/station_edit_page.html', context)


@login_required
def set_primary_station_image(request, pk):
    image = get_object_or_404(StationImage, pk=pk)

    if (not image.station.owner_group == request.user.group and
            not request.user.is_administrator()):
        return HttpResponseForbidden()

    station_images = StationImage.objects.filter(station=image.station)
    for img in station_images:
        img.is_primary = False
        img.save()

    image.is_primary = True
    image.save()

    return HttpResponseRedirect('/stations/{0}/edit/'.format(image.station.id))


@login_required
def delete_station_image(request, pk):
    image = get_object_or_404(StationImage, pk=pk)

    if (not image.station.owner_group == request.user.group and
            not request.user.is_administrator()):
        return HttpResponseForbidden()

    if not image.is_primary:
        if os.path.isfile(image.image.path):
            os.remove(image.image.path)
        image.delete()

        return HttpResponseRedirect('/stations/{0}/edit/'.format(image.station.id))

    return HttpResponseForbidden()


@login_required
def station_add_page(request):
    if request.method == 'POST':
        # Use custom PartialStationForm to validate form datas
        # is_valid() will be true if received data is good
        # There'll be error messages in 'form' instance if validation failed
        # cleaned_data will be the form inputs from the request
        form = PartialStationForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            station = form.save(commit=False)
            station.location = Point(x=data['lng'], y=data['lat'])
            station.save()
            # save first
            # need an instance to add beacons
            station.beacon_set.add(Beacon.objects.get(name=data['beacon']))
            station.save()

            # Add images
            for key, value in data.items():
                if isinstance(value, UploadedFile):
                    is_primary = (key == 'img{0}'.format(data['main_img_num']))
                    StationImage.objects.create(
                        station=station,
                        image=value,
                        is_primary=is_primary
                    )

            return HttpResponseRedirect('/stations/')
    else:
        form = PartialStationForm()

    if request.user.can(Permission.ADMIN):
        beacon_set = Beacon.objects.all()
        user_groups = UserGroup.objects.all().order_by('id')
    elif request.user.can(Permission.EDIT):
        beacon_set = Beacon.objects.filter(owner_group=request.user.group)
        user_groups = UserGroup.objects.filter(name=request.user.group)
    else:
        return HttpResponseForbidden()

    context = {
        'categories': StationCategory.objects.all().order_by('id'),
        'beacons': beacon_set,
        'form': form,
        'max_imgs': settings.MAX_IMGS_UPLOAD,
        'user_groups': user_groups,
    }
    return render(request, 'app/station_add_page.html', context)


@csrf_exempt
def get_all_rewards(request):
    """API for retrieving rewards list"""
    data = [
        {
            'id': reward.id,
            'name': reward.name,
            'image_url': 'http://{0}/{1}'.format(request.get_host(), reward.image.url)
        }
        for reward in Reward.objects.all()
    ]

    return JsonResponse(
        data={'data': data},
        status=200,
        json_dumps_params={'ensure_ascii': False},
        content_type='application/json; charset=utf-8'
    )


@csrf_exempt
def get_all_stations(request):
    """API for retrieving contents of all Stations

    Returns:
        data (:obj: `list` of :obj: `dict`): a json-liked dict formating with::
            {
                'id': station's id,
                'name': statione's name,
                'content': station's infomation content,
                'category' (data: what category station belongs to,
                'location': station's location,
                'rewards': list of
                'image': {
                    'primary': primary image url,
                    'others': list of the other image url
                }
            }

    """
    stations = Station.objects.all()
    prefix = 'https://' if request.is_secure() else 'http://'
    domain = request.get_host()

    data = [
        {
            'id': station.id,
            'name': station.name,
            'content': station.content,
            'category': str(station.category),
            'location': station.location.get_coords(),
            'rewards': [reward.id for reward in station.reward_set.all()],
            'image': {
                'primary':
                    '{0}{1}{2}'.format(
                        prefix,
                        domain,
                        station.get_primary_image()
                    )
                    if station.get_primary_image() else '',
                'others': [
                    '{0}{1}{2}'.format(prefix, domain, image_url)
                    for image_url in station.get_other_images()
                ]
            }
        }
        for station in stations
    ]

    return JsonResponse(
        data={'data': data},
        status=200,
        json_dumps_params={'ensure_ascii': False},
        content_type='application/json; charset=utf-8'
    )


@csrf_exempt
@require_POST
def get_linked_stations(request):
    """API for retrieving list of stations linked to the Beacon"""
    beacon_id = request.POST.get('beacon_id')
    user_email = request.POST.get('email')

    user = User.objects.filter(email=user_email).first()
    if not user:
        return HttpResponse('User does not exist', status=404)

    beacon = Beacon.objects.filter(beacon_id=beacon_id).first()
    if beacon:
        UserVisitedBeacons.objects.create(user=user, beacon=beacon)

    stations = Station.objects.filter(beacon__beacon_id=beacon_id)
    if not stations:
        return HttpResponse('No match stations', status=404)
    else:
        data = [station.id for station in stations]

        return JsonResponse(data={'data': data}, status=200)


@csrf_exempt
@require_POST
def update_user_coins(request):
    coins = request.POST.get('coins')
    user_email = request.POST.get('email')

    user = User.objects.filter(email=user_email).first()

    if not user or not coins:
        return HttpResponse('Either user does not exist or coins input is not given', status=404)

    try:
        user.earned_coins = coins
        user.save()
    except ValueError:
        return HttpResponse('Invalid input of coins', status=400)

    data = {
        'message': 'Coins record of {0} update succeed'.format(user_email),
        'data': {'coins': user.earned_coins}
    }

    return JsonResponse(data=data, status=200)


@csrf_exempt
@require_POST
def update_user_experience_point(request):
    experience_point = request.POST.get('experience_point')
    user_email = request.POST.get('email')

    user = User.objects.filter(email=user_email).first()

    if not user or not experience_point:
        return HttpResponse('Either user does not exist or experience_point input is not given', status=404)

    try:
        user.experience_point = experience_point
        user.save()
    except ValueError:
        return HttpResponse('Invalid input of experience point', status=400)

    data = {
        'message': 'Experience point record of {0} update succeed'.format(user_email),
        'data': {'experience_point': user.experience_point}
    }

    return JsonResponse(data=data, status=200)


@csrf_exempt
@require_POST
def add_user_reward(request):
    """POST a reward id and update the user data"""
    user_email = request.POST.get('email')
    reward_id = request.POST.get('reward_id')

    user = User.objects.filter(email=user_email).first()
    reward = Reward.objects.filter(id=reward_id).first()

    if not user or not reward:
        return HttpResponse('Either user or reward does not exist.', status=404)

    try:
        UserReward.objects.create(user=user, reward=reward)
    except ValueError:
        return HttpResponse('Add user reward failed.', status=400)

    return HttpResponse('Create Succeeded', status=200)


@csrf_exempt
@require_POST
def add_user_favorite_stations(request):
    station_id = request.POST.get('station_id')
    user_email = request.POST.get('email')

    station = Station.objects.filter(id=station_id).first()
    user = User.objects.filter(email=user_email).first()

    if not user or not station:
        return HttpResponse('Either user or station does not exist', status=404)

    user.favorite_stations.add(station)
    user.save()

    return JsonResponse(
        data={
                "message": "Favorite stations update succeed",
                "stations": [station.id for station in user.favorite_stations.all()]
        },
        status=200
    )


@login_required
def category_add_page(request):
    if request.method == 'POST':
        category_form = StationCategoryForm(request.POST)

        if category_form.is_valid():
            if request.user.can(Permission.ADMIN):
                stations = Station.objects.all()
            elif request.user.can(Permission.EDIT):
                stations = Station.objects.filter(
                    owner_group=request.user.group
                )
            else:
                return HttpResponseForbidden()

            category_form.save()

            return HttpResponseRedirect('/stations/')

    context = {
        'categories': StationCategory.objects.all().order_by('id')
    }

    return render(request, 'app/category_add_page.html', context)


@csrf_exempt
@require_POST
def remove_user_favorite_stations(request):
    station_id = request.POST.get('station_id')
    user_email = request.POST.get('email')

    station = Station.objects.filter(id=station_id).first()
    user = User.objects.filter(email=user_email).first()

    if not user or not station:
        return HttpResponse('Either user or station does not exist', status=404)

    user.favorite_stations.remove(station)
    user.save()

    return JsonResponse(
        data={
                "message": "Favorite stations update succeed",
                "stations": [station.id for station in user.favorite_stations.all()]
        },
        status=200
    )


@csrf_exempt
def get_all_travel_plans(request):
    data = [
        {
            'id': plan.id,
            'name': plan.name,
            'description': plan.description,
            'station_sequence': [travelplanstation.station.id
                                 for travelplanstation in plan.travelplanstations_set.all().order_by('order')],
            'image': 'http://{0}{1}'.format(request.get_host(), plan.image.url)
        }
        for plan in TravelPlan.objects.all()
    ]

    return JsonResponse(
        data={'data': data},
        status=200,
        json_dumps_params={'ensure_ascii': False},
        content_type='application/json; charset=utf-8'
    )


@login_required
def reward_list_page(request):

    context = {
        'rewards': Reward.objects.all(),
        'categories': StationCategory.objects.all().order_by('id')
    }

    return render(request, 'app/reward_list_page.html', context)


@login_required
def reward_add_page(request):
    if request.method == 'POST':
        reward_form = PartialRewardForm(request.POST, request.FILES)

        if reward_form.is_valid():
            reward_form.save()

            context = {
                'rewards': Reward.objects.all(),
                'categories': StationCategory.objects.all().order_by('id')
            }

            return render(request, 'app/reward_list_page.html', context)

    context = {
        'categories': StationCategory.objects.all().order_by('id')
    }

    return render(request, 'app/reward_add_page.html', context)


@login_required
@administrator_required
def reward_edit_page(request, pk):
    reward = get_object_or_404(Reward, pk=pk)
    if request.method == 'POST':
        reward_form = RewardForm(request.POST, request.FILES, instance=reward)

        if reward_form.is_valid():
            reward_form.save()

            return HttpResponseRedirect('/rewards/')

    if request.user.is_administrator():
        stations = Station.objects.all().order_by('id')
    else:
        stations = Station.objects.filter(owner_group=request.user.group).order_by('id')

    form_data = {
        'name': reward.name,
        'description': reward.description,
        'related_station': reward.related_station,
        'image': reward.image
    }
    context = {
        'categories': StationCategory.objects.all().order_by('id'),
        'stations': stations,
        'form_data': form_data
    }
    return render(request, 'app/reward_edit_page.html', context)


@login_required
def reward_delete_page(request, pk):
    reward = get_object_or_404(Reward, pk=pk)
    reward.delete()

    return HttpResponseRedirect('/rewards/')


@login_required
def manager_list_page(request):
    manager_list = User.objects.exclude(role__name='User').order_by('email')
    paginator = Paginator(manager_list, 10)

    # Try to get the page number
    page = request.GET.get('page', 1)
    try:
        managers = paginator.page(page)
    except PageNotAnInteger:
        managers = paginator.page(1)
    except EmptyPage:
        # Page Number is out of range
        managers = paginator.page(paginator.num_pages)

    context = {
        'managers': managers,
        'categories': StationCategory.objects.all().order_by('id')
    }

    return render(request, 'app/manager_list_page.html', context)


@login_required
@administrator_required
def manager_add_page(request):
    if request.method == 'POST':
        form = ManagerForm(request.POST)
        password = request.POST.get('password')

        if form.is_valid() and password is not None:
            data = form.cleaned_data
            manager = form.save(commit=False)
            manager.set_password(password)
            manager.save()
            return HttpResponseRedirect('/managers/')
    else:
        form = ManagerForm()

    roles = Role.objects.exclude(name='User')
    groups = UserGroup.objects.all()
    context = {
        'roles': roles,
        'groups': groups,
        'form': form,
        'categories': StationCategory.objects.all().order_by('id'),
    }

    return render(request, 'app/manager_add_page.html', context)


@login_required
@administrator_required
def manager_edit_page(request, pk):
    manager = get_object_or_404(User, pk=pk)

    if request.user == manager:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ManagerForm(request.POST, instance=manager)
        password = request.POST.get('password')

        if form.is_valid():
            data = form.cleaned_data
            manager = form.save(commit=False)
            if password:
                manager.set_password(password)
            manager.save()
            return HttpResponseRedirect('/managers/')
    else:
        form = ManagerForm()

    form_data = {
        'email': manager.email,
        'role': manager.role,
        'group': manager.group,
        'nickname': manager.nickname,
    }

    roles = Role.objects.exclude(name='User')
    groups = UserGroup.objects.all()
    context = {
        'roles': roles,
        'groups': groups,
        'form': form,
        'form_data': form_data,
        'categories': StationCategory.objects.all().order_by('id'),
    }

    return render(request, 'app/manager_edit_page.html', context)


@login_required
@administrator_required
def manager_delete_page(request, pk):
    manager = get_object_or_404(User, pk=pk)
    manager.delete()

    return HttpResponseRedirect('/managers/')


@login_required
@administrator_required
def beacon_list_page(request):
    beacon_list = Beacon.objects.all().order_by('beacon_id')
    paginator = Paginator(beacon_list, 10)

    # Try to get the page number
    page = request.GET.get('page', 1)
    try:
        beacons = paginator.page(page)
    except PageNotAnInteger:
        beacons = paginator.page(1)
    except EmptyPage:
        beacons = paginator.page(paginator.num_pages)

    context = {
        'categories': StationCategory.objects.all().order_by('id'),
        'beacons': beacons
    }

    return render(request, 'app/beacon_list_page.html', context)


@login_required
@administrator_required
def beacon_add_page(request):
    if request.method == 'POST':
        form = BeaconForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            beacon = form.save(commit=False)
            beacon.location = Point(x=data['lng'], y=data['lat'])
            beacon.save()
            return HttpResponseRedirect('/beacons/')
    else:
        form = BeaconForm()

    context = {
        'groups': UserGroup.objects.all(),
        'form': form
    }

    return render(request, 'app/beacon_add_page.html', context)


@login_required
@administrator_required
def beacon_edit_page(request, pk):
    beacon = get_object_or_404(Beacon, pk=pk)

    if request.method == 'POST':
        form = BeaconForm(request.POST, instance=beacon)

        if form.is_valid():
            data = form.cleaned_data
            beacon = form.save(commit=False)
            beacon.location = Point(x=data['lng'], y=data['lat'])
            beacon.save()
            return HttpResponseRedirect('/beacons/')
    else:
        form = BeaconForm()

    form_data = {
        'beacon_id': beacon.beacon_id,
        'name': beacon.name,
        'description': beacon.description,
        'lat': beacon.location.y,
        'lng': beacon.location.x,
        'owner_group': beacon.owner_group
    }

    context = {
        'groups': UserGroup.objects.all().order_by('id'),
        'form': form,
        'form_data': form_data
    }

    return render(request, 'app/beacon_edit_page.html', context)


@login_required
@administrator_required
def beacon_delete_page(request, pk):
    beacon = get_object_or_404(Beacon, pk=pk)
    beacon.delete()

    return HttpResponseRedirect('/beacons/')


@login_required
def station_delete_page(request, pk):
    station = get_object_or_404(Station, pk=pk)

    if (not station.owner_group == request.user.group and
            not request.user.is_administrator()):
        return HttpResponseForbidden()

    station.delete()

    return HttpResponseRedirect('/stations/')


@login_required
def travelplan_list_page(request):
    context = {
        'categories': StationCategory.objects.all(),
        'travelplans': TravelPlan.objects.all().order_by('id')
    }

    return render(request, 'app/travelplan_list_page.html', context)


@login_required
def travelplan_add_page(request):
    if request.method == 'POST':
        travelplan_form = PartialTravelPlanForm(request.POST, request.FILES)

        if travelplan_form.is_valid():
            travelplan_form.save()

            context = {
                'categories': StationCategory.objects.all().order_by('id'),
                'travelplans': TravelPlan.objects.all()
            }

            return HttpResponseRedirect('/travelplans/')
    else:
        travelplan_form = PartialTravelPlanForm()

    context = {
        'categories': StationCategory.objects.all().order_by('id'),
        'form': travelplan_form
    }

    return render(request, 'app/travelplan_add_page.html', context)


@login_required
def travelplan_edit_page(request, pk):
    travelplan = get_object_or_404(TravelPlan, pk=pk)

    if request.method == 'POST':
        travelplan_form = PartialTravelPlanForm(
            request.POST,
            request.FILES,
            instance=travelplan
        )

        if travelplan_form.is_valid():
            edited_travelplan = travelplan_form.save()
            json_order = json.loads(request.POST['order'])
            exist_travelplan_stations = [
                travelplan_station.station_id
                for travelplan_station in TravelPlanStations.objects.filter(travelplan_id=pk)
            ]

            for order, station_id in enumerate(json_order):
                changed_travelplan = TravelPlanStations.objects.filter(
                    travelplan_id=pk,
                    station_id=station_id
                )
                if not changed_travelplan:
                    TravelPlanStations.objects.create(
                        travelplan_id=pk,
                        station_id=station_id,
                        order=order
                    )
                else:
                    changed_travelplan.first().order = order
                    changed_travelplan.first().save()
                    exist_travelplan_stations.remove(int(station_id))

            for station_id in exist_travelplan_stations:
                TravelPlanStations.objects.filter(
                    travelplan=travelplan,
                    station_id=station_id
                ).delete()

            context = {
                'categories': StationCategory.objects.all().order_by('id'),
                'travelplans': TravelPlan.objects.all()
            }

            return HttpResponseRedirect('/travelplans/')
        form_data = travelplan_form.cleaned_data

    else:
        form_data = {
            'name': travelplan.name,
            'description': travelplan.description
        }

    selected_stations = Station.objects.filter(
        travelplanstations__travelplan_id=pk
    ).order_by('travelplanstations__order')

    context = {
        'stations': Station.objects.exclude(travelplanstations__travelplan_id=pk),
        'travelplan': travelplan,
        'selected_stations': selected_stations,
        'form_data': form_data,
        'categories': StationCategory.objects.all().order_by('id')
    }

    return render(request, 'app/travelplan_edit_page.html', context)


@login_required
def travelplan_delete_page(request, pk):
    travelplan = get_object_or_404(TravelPlan, pk=pk)
    travelplan_stations = TravelPlanStations.objects.filter(travelplan_id=pk)

    travelplan_stations.delete()
    travelplan.delete()

    return HttpResponseRedirect('/travelplans/')


@login_required
@administrator_required
def group_list_page(request):
    group_list = UserGroup.objects.all().order_by('id')
    paginator = Paginator(group_list, 10)

    page = request.GET.get('page', 1)
    try:
        groups = paginator.page(page)
    except PageNotAnInteger:
        groups = paginator.page(1)
    except EmptyPage:
        groups = paginator.page(paginator.num_pages)

    context = {
        'categories': StationCategory.objects.all().order_by('id'),
        'groups': groups
    }

    return render(request, 'app/group_list_page.html', context)


@login_required
@administrator_required
def group_add_page(request):
    if request.method == 'POST':
        group_name = request.POST.get('name')

        if group_name:
            try:
                UserGroup.objects.create(name=group_name)
                return HttpResponseRedirect('/groups/')
            except IntegrityError:
                messages.warning(request, 'This group name already exists!')
        else:
            messages.warning(request, 'Group name input is not given!')

    context = {
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/group_add_page.html', context)


@login_required
@administrator_required
def group_edit_page(request, pk):
    group_instance = get_object_or_404(UserGroup, pk=pk)

    if request.method == 'POST':
        group_name = request.POST.get('name')

        if group_name:
            try:
                group_instance.name = group_name
                group_instance.save()
                return HttpResponseRedirect('/groups/')
            except IntegrityError:
                messages.warning(request, 'This group name already exists!')
        else:
            messages.warning(request, 'Group name input is not given!')

    context = {
        'categories': StationCategory.objects.all(),
        'group': group_instance.name
    }

    return render(request, 'app/group_edit_page.html', context)


@login_required
def question_list_page(request):
    if request.user.is_administrator():
        stations = Station.objects.all()
        question_list = Question.objects.all().order_by('id')
    else:
        stations = Station.objects.filter(owner_group=request.user.group)
        question_list = Question.objects.filter(
            linked_station__in=stations
        ).order_by('id')

    paginator = Paginator(question_list, 10)

    page = request.GET.get('page', 1)
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)

    context = {
        'questions': questions,
        'categories': StationCategory.objects.all().order_by('id')
    }

    return render(request, 'app/question_list_page.html', context)


@login_required
def question_add_page(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)

        if form.is_valid():
            question = form.save()

            choice_contents = request.POST.getlist('choice_contents')
            # The post will send a choice content list,
            # and a answer_order to indicate which one in te list is the answer
            answer_order = int(request.POST.get('answer', 1))

            for order, choice_contnet in enumerate(choice_contents, start=1):
                if answer_order == order:
                    Choice.objects.create(
                        question=question,
                        content=choice_contnet,
                        is_answer=True
                    )
                else:
                    Choice.objects.create(
                        question=question,
                        content=choice_contnet,
                        is_answer=False
                    )
            return HttpResponseRedirect('/questions/')
    else:
        form = QuestionForm()

    if request.user.is_administrator():
        stations = Station.objects.all()
    else:
        stations = Station.objects.filter(owner_group=request.user.group)

    context = {
        'categories': StationCategory.objects.all().order_by('id'),
        'stations': stations.order_by('id')
    }
    return render(request, 'app/question_add_page.html', context)


@login_required
def question_edit_page(request, pk):
    question = get_object_or_404(Question, pk=pk)

    # The post will send the choice model id to indicate which one to edit
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)

        if form.is_valid():
            form.save()

            edited_contents = request.POST.getlist('choice_contents')
            choice_ids = request.POST.getlist('choice_ids')
            answer_id = int(request.POST.get('answer', 1))
            question_choices = Choice.objects.filter(question=question)

            for question_choice in question_choices:
                question_choice.is_answer = False
                question_choice.save()

            for edited_content, choice_id in zip(edited_contents, choice_ids):
                edited_choice = Choice.objects.get(
                    id=choice_id
                )
                edited_choice.content = edited_content
                edited_choice.save()

            answer_choice = Choice.objects.get(id=answer_id)
            answer_choice.is_answer = True
            answer_choice.save()
            return HttpResponseRedirect('/questions/')

        form_data = form.cleaned_data
        form_data['choices'] = request.POST.getlist('choices')
        form_data['answer_id'] = request.POST.get('answer', 1)
    else:
        form = QuestionForm()

    if request.user.is_administrator():
        stations = Station.objects.all()
    else:
        stations = Station.objects.filter(owner_group=request.user.group)

    question_choices = Choice.objects.filter(
        question=question
    ).order_by('id')

    form_data = {
        'content': question.content,
        'linked_station': question.linked_station,
        'choices': [
            choice
            for choice in question_choices
        ],
        'answer_id': Choice.objects.filter(
            question=question,
            is_answer=True
        ).first().id
    }

    context = {
        'categories': StationCategory.objects.all().order_by('id'),
        'form': form,
        'form_data': form_data,
        'stations': stations
    }
    return render(request, 'app/question_edit_page.html', context)


@login_required
def question_delete_page(request, pk):
    question = get_object_or_404(Question, pk=pk)
    question.delete()

    return HttpResponseRedirect('/questions/')


@csrf_exempt
def station_search_page(request):
    query = request.GET.get('query', 1)
    if request.user.can(Permission.ADMIN):
        station_list = Station.objects.filter(
            name__contains=query
        ).order_by('id')
    else:
        station_list = Station.objects.filter(
            name__contains=query,
            owner_group=request.user.group
        ).order_by('id')

    paginator = Paginator(station_list, 10)

    page = request.GET.get('page', 1)
    try:
        stations = paginator.page(page)
    except PageNotAnInteger:
        stations = paginator.page(1)
    except EmptyPage:
        stations = paginator.page(paginator.num_pages)

    for station in stations:
        station.primary_image = StationImage.objects.filter(
            station=station,
            is_primary=True
        ).first()
        station.beacon = Beacon.objects.filter(
            station=station
        ).first()

    context = {
        'stations': stations,
        'categories': StationCategory.objects.all().order_by('id')
    }

    return render(request, 'app/station_list_page.html', context)


@login_required
@administrator_required
def beacon_search_page(request):

    query = request.GET.get('query', 1)
    beacon_list = Beacon.objects.filter(
        beacon_id__contains=query
    ).order_by('beacon_id')
    paginator = Paginator(beacon_list, 10)

    # Try to get the page number
    page = request.GET.get('page', 1)
    try:
        beacons = paginator.page(page)
    except PageNotAnInteger:
        beacons = paginator.page(1)
    except EmptyPage:
        beacons = paginator.page(paginator.num_pages)

    context = {
        'categories': StationCategory.objects.all(),
        'beacons': beacons
    }

    return render(request, 'app/beacon_list_page.html', context)


@login_required
@administrator_required
def group_delete_page(request, pk):
    group_instance = get_object_or_404(UserGroup, pk=pk)
    group_instance.delete()

    return HttpResponseRedirect('/groups/')


@require_GET
@csrf_exempt
def get_unanswered_question(request):
    station_id = request.GET.get('station_id')
    user_email = request.GET.get('email')

    station = Station.objects.filter(id=station_id).first()
    user = User.objects.filter(email=user_email).first()

    if not user or not station:
        return HttpResponse('Either user or station does not exist', status=400)

    unanswered_questions = Question.objects.exclude(
        user__pk=user_email
    ).filter(linked_station=station)

    if not unanswered_questions:
        return JsonResponse(data={}, status=200)

    random_index = random.randint(0, unanswered_questions.count() - 1)
    random_unanswered_question = random.sample(list(unanswered_questions), 1)[0]

    choices = []
    for i, choice in enumerate(Choice.objects.filter(question=random_unanswered_question)):
        choices.append(choice.content)
        if choice.is_answer:
            index = i + 1

    return JsonResponse(
        data={
            'content': random_unanswered_question.content,
            'choices': choices,
            'answer': index,
            'question_id': random_unanswered_question.id
        },
        status=200,
        json_dumps_params={'ensure_ascii': False},
        content_type='application/json; charset=utf-8'
    )


@require_POST
@csrf_exempt
def add_answered_question(request):
    question_id = request.POST.get('question_id')
    user_email = request.POST.get('email')

    question = Question.objects.filter(id=question_id).first()
    user = User.objects.filter(email=user_email).first()

    if not user or not question:
        return HttpResponse('Either user or question does not exist', status=400)

    user.answered_questions.add(question)

    return HttpResponse('Add answered question succeeded', status=200)


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.email_confirmed = True
        user.save()
        return HttpResponse('Your email is activated.', status=200)

    return HttpResponse('Activation link is invalid.', status=401)


@csrf_exempt
@require_POST
@activate_required
def reset_password(request, email):
    message = render_to_string('email/reset_password.html', {
        'prefix': 'https://' if request.is_secure() else 'http://',
        'user': request.user,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(request.user.pk)),
        'token': default_token_generator.make_token(request.user),
        'expired_days': settings.PASSWORD_RESET_TIMEOUT_DAYS
    })
    mail_subject = '[NCKU Smart Campus App] Reset account password'
    email = EmailMessage(mail_subject, message, to=[request.user.email])
    email.send()

    return HttpResponse('Reset password email is been sent.', status=200)


@csrf_exempt
def reset_password_page(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if not user or not default_token_generator.check_token(user, token):
        return HttpResponse('Reset Password link is invalid.', status=401)

    if request.method == 'POST':
        password = request.POST.get('password')
        user.set_password(password)
        user.save()

        return HttpResponse('Reset password succeeded', status=200)

    context = {
        'user': user
    }

    return render(request, 'app/reset_password_page.html', context)


@login_required
def manager_edit_self_page(request, pk):
    manager = get_object_or_404(User, pk=pk)

    if request.user != manager:
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = PartialManagerForm(request.POST, instance=manager)
        password = request.POST.get('password')

        if form.is_valid():
            data = form.cleaned_data
            manager = form.save(commit=False)
            if password:
                manager.set_password(password)
            manager.save()
            return HttpResponseRedirect('/managers/')
    else:
        form = PartialManagerForm()

    form_data = {
        'email': manager.email,
        'nickname': manager.nickname,
    }

    context = {
        'form': form,
        'form_data': form_data,
        'categories': StationCategory.objects.all().order_by('id'),
    }

    return render(request, 'app/manager_edit_self_page.html', context)


@csrf_exempt
@require_POST
def resend_activation(request, email):
    try:
        user = User.objects.get(email=email)
    except (TypeError, ValueError, OverflowError, User.DoestNotExist):
        return HttpResponse('The user does not exist.', status=400)
    if user.email_confirmed:
        return HttpResponse('The user is already activated.', status=401)

    message = render_to_string('email/activation.html', {
        'prefix': 'https://' if request.is_secure() else 'http://',
        'user': user,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
        'expired_days': settings.PASSWORD_RESET_TIMEOUT_DAYS
    })
    mail_subject = '[NCKU Smart Campus App] Please activate your account'
    email = EmailMessage(mail_subject, message, to=[user.email])
    email.send()

    return HttpResponse('The activation email is sent!', status=201)


@login_required
def beacon_heatmap_page(request):
    return render(request, 'extra/heatmap.html')


@login_required
def get_beacon_detect_data(request):
    data = [
        {
            'beacon_id': visit_record.beacon.name,
            'lat': visit_record.beacon.location.y,
            'lng': visit_record.beacon.location.x,
            'date': str(visit_record.timestamp.astimezone(pytz.timezone('Asia/Taipei')).date()),
            'time': str(visit_record.timestamp.astimezone(pytz.timezone('Asia/Taipei')).time()),
        }
        for visit_record in UserVisitedBeacons.objects.all()
    ]

    return JsonResponse(data={'data': data}, status=200)
