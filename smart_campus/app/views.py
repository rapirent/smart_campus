from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
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
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

import os
import random
import json

from .models import (
    User, Reward, Permission,
    Station, StationCategory,
    Beacon, StationImage, Question,
    UserReward, UserGroup,
    TravelPlan, Role,
    TravelPlanStations,
    Choice, QuestionChoice
)
from .forms import (
    StationForm,
    StationCategoryForm,
    ManagerForm,
    PartialRewardForm,
    PartialTravelPlanForm,
    RewardForm,
    BeaconForm,
    QuestionForm
)


@csrf_exempt
@require_POST
def signup(request):
    """Signup API for APP users

    Register new users

    """
    email = request.POST.get('email')
    password = request.POST.get('password')
    nickname = request.POST.get('nickname', '')

    if not email or not password:
        return HttpResponse('Either email or password input is missing.', status=400)

    if User.objects.filter(email=email).exists():
        return HttpResponse('The email is already taken, try another!', status=400)

    try:
        User.objects.create_user(email, password, nickname)
    except ValueError:
        return HttpResponse('Invalid email address.', status=400)

    return HttpResponse('Registration succeeded!', status=200)


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
            'reward': [reward.id for reward in UserReward.objects.filter(user=user).order_by('timestamp')],
            'favorite_stations': [station.id for station in user.favorite_stations.all()],
        }
        return JsonResponse(data={'message': 'Login success', 'data': user_data}, status=200, json_dumps_params={'ensure_ascii': False}, content_type='application/json; charset=utf-8')

    return HttpResponse('Login failed', status=401)


@csrf_exempt
@require_POST
def logout(request):
    """Logout API for APP users

    Handle logout requests from app

    """
    email = request.POST.get('email')
    request.user = User.objects.filter(email=email).first()

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
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = auth.authenticate(request, username=email, password=password)

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
    categories = StationCategory.objects.all()
    context = {'email': request.user.email, 'categories': categories}
    return render(request, 'app/index.html', context)


@login_required
def station_list_page(request):
    """Show all stations managed by the user's group"""
    if request.user.can(Permission.ADMIN):
        stations = Station.objects.all().order_by('id')
    else:
        stations = Station.objects.filter(
            owner_group=request.user.group
        ).order_by('id')

    station_data = [
        {
            'id': station.id,
            'name': station.name,
            'primary_image': StationImage.objects.filter(
                station=station,
                is_primary=True
            ).first(),
            'category': station.category,
            'beacon': Beacon.objects.filter(
                station=station
            ).first()
        }
        for station in stations
    ]

    context = {
        'email': request.user.email,
        'stations': station_data,
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/station_list.html', context)


@login_required
def station_list_by_category_page(request, pk):
    category = get_object_or_404(StationCategory, pk=pk)
    if request.user.can(Permission.ADMIN):
        stations = Station.objects.filter(category=category)
    else:
        stations = Station.objects.filter(owner_group=request.user.group, category=category)

    station_data = [
        {
            'id': station.id,
            'name': station.name,
            'primary_image': StationImage.objects.filter(
                    station=station,
                    is_primary=True
                ).first(),
            'category': station.category,
            'beacon': Beacon.objects.filter(
                station=station
            ).first()
        }
        for station in stations
    ]

    context = {
        'email': request.user.email,
        'stations': station_data,
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/station_list.html', context)


@login_required
def station_edit_page(request, pk):
    station = get_object_or_404(Station, pk=pk)

    if (not station.owner_group == request.user.group and
            not request.user.is_administrator()):
        return HttpResponseForbidden()

    if request.method == 'POST':
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

            # Add new images
            for key, value in data.items():
                if isinstance(value, InMemoryUploadedFile):
                    StationImage.objects.create(
                        station=station,
                        image=value,
                        is_primary=False
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
            'lat': station.location.y,
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
        'images': StationImage.objects.filter(station_id=station.id)
    }
    return render(request, 'app/station_edit.html', context)


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
    data = [
        {
            'id': reward.id,
            'name': reward.name,
            'image_url': 'http://{0}/{1}'.format(request.get_host(), reward.image.url)
        }
        for reward in Reward.objects.all()
    ]

    return JsonResponse(data={'data': data}, status=200, json_dumps_params={'ensure_ascii': False}, content_type='application/json; charset=utf-8')


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
            'rewards': [station.id for station in station.reward_set.all()],
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

    stations = Station.objects.filter(beacon__beacon_id=beacon_id)
    if not stations:
        return HttpResponse('No match stations', status=404)
    else:
        data = [station.id for station in stations]

        return JsonResponse(data={'data': data}, status=200)


@csrf_exempt
@require_POST
def get_unanswered_question(request):
    """API requesting a single question"""
    station_id = request.POST.get('station_id')
    email = request.POST.get('email')

    station = Station.objects.filter(id=station_id).first()
    user = User.objects.filter(email=email).first()

    if not user or not station:
        return HttpResponse('Either user or station does not exist', status=400)

    questions = Question.objects.filter(linked_station=station)
    user_answered_questions = Question.objects.filter(user=user)

    # Get questions that the user hasn't answered yet
    not_answered_questions = questions.difference(user_answered_questions)

    if not_answered_questions.exists():
        # pick 1 question randomly
        question = random.sample(list(not_answered_questions), 1)[0]
        ans = question.choices.filter(questionchoice__is_answer=True).first()
        data = {
            'content': question.content,
            'type': question.question_type,
            'choices': [choice.content for choice in question.choices.all()],
            'answer': ans.content
        }
        # Add to answered questions
        user.answered_questions.add(question)

        return JsonResponse(data=data, status=200)

    return HttpResponse('No unanswered question available for the user', status=404)


@csrf_exempt
@require_POST
def update_user_coins(request):
    coins = request.POST.get('coins')
    email = request.POST.get('email')

    user = User.objects.filter(email=email).first()

    if not user or not coins:
        return HttpResponse('Either user does not exist or coins input is not given', status=400)

    try:
        user.earned_coins = coins
        user.save()
    except ValueError:
        return HttpResponse('Invalid input of coins', status=400)

    data = {
        'message': 'Coins record of {0} successfully updated'.format(email),
        'data': {'coins': user.earned_coins}
    }

    return JsonResponse(data=data, status=200)


@csrf_exempt
@require_POST
def update_user_experience_point(request):
    experience_point = request.POST.get('experience_point')
    email = request.POST.get('email')

    user = User.objects.filter(email=email).first()

    if not user or not experience_point:
        return HttpResponse('Either user does not exist or experience_point input is not given', status=400)

    try:
        user.experience_point = experience_point
        user.save()
    except ValueError:
        return HttpResponse('Invalid input of experience point', status=400)

    data = {
        'message': 'Experience point record of {0} successfully updated'.format(email),
        'data': {'experience_point': user.experience_point}
    }

    return JsonResponse(data=data, status=200)


@csrf_exempt
@require_POST
def add_user_reward(request):
    """POST a reward id and update the user data"""
    email = request.POST.get('email')
    reward_id = request.POST.get('reward_id')

    user = User.objects.filter(email=email).first()
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
    email = request.POST.get('email')

    station = Station.objects.filter(id=station_id).first()
    user = User.objects.filter(email=email).first()

    if not user or not station:
        return HttpResponse('Either user or station does not exist', status=400)

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
        'email': request.user.email,
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/category_add_page.html', context)


@csrf_exempt
@require_POST
def remove_user_favorite_stations(request):
    station_id = request.POST.get('station_id')
    email = request.POST.get('email')

    station = Station.objects.filter(id=station_id).first()
    user = User.objects.filter(email=email).first()

    if not user or not station:
        return HttpResponse('Either user or station does not exist', status=400)

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
                                 for travelplanstation in plan.travelplanstations_set.all().order_by('order')]
        }
        for plan in TravelPlan.objects.all()
    ]

    return JsonResponse(data={'data': data}, status=200, json_dumps_params={'ensure_ascii': False}, content_type='application/json; charset=utf-8')


@login_required
def reward_list_page(request):

    context = {
        'email': request.user.email,
        'rewards': Reward.objects.all(),
        'categories': StationCategory.objects.all()
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
                'email': request.user.email,
                'categories': StationCategory.objects.all()
            }

            return render(request, 'app/reward_list_page.html', context)

    context = {
        'email': request.user.email,
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/reward_add_page.html', context)


@login_required
def reward_edit_page(request, pk):
    reward = get_object_or_404(Reward, pk=pk)
    if request.method == 'POST':
        reward_form = RewardForm(request.POST, request.FILES, instance=reward)

        if reward_form.is_valid():
            reward_form.save()

            return HttpResponseRedirect('/rewards/')

    if request.user.is_administrator():
        stations = Station.objects.all()
    else:
        stations = Station.objects.filter(owner_group=request.user.group)

    form_data = {
        'name': reward.name,
        'description': reward.description,
        'related_station': reward.related_station
    }
    context = {
        'email': request.user.email,
        'categories': StationCategory.objects.all(),
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
    if not request.user.is_administrator():
        return HttpResponseForbidden()

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
        'email': request.user.email,
        'managers': User.objects.exclude(role__name='User'),
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/manager_list_page.html', context)


@login_required
def manager_add_page(request):
    if not request.user.is_administrator():
        return HttpResponseForbidden()

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
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/manager_add_page.html', context)


@login_required
def manager_edit_page(request, pk):
    if not request.user.is_administrator():
        return HttpResponseForbidden()

    manager = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = ManagerForm(request.POST, instance=manager)

        if form.is_valid():
            data = form.cleaned_data
            form.save()
            return HttpResponseRedirect('/managers/')
    else:
        form = ManagerForm()

    form_data = {
        'email': manager.email,
        'role': manager.role,
        'group': manager.group
    }

    roles = Role.objects.exclude(name='User')
    groups = UserGroup.objects.all()
    context = {
        'roles': roles,
        'groups': groups,
        'form': form,
        'form_data': form_data,
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/manager_edit_page.html', context)


@login_required
def manager_delete_page(request, pk):
    if not request.user.is_administrator():
        return HttpResponseForbidden()

    manager = get_object_or_404(User, pk=pk)
    manager.delete()

    return HttpResponseRedirect('/managers/')


@login_required
def beacon_list_page(request):
    if not request.user.is_administrator():
        return HttpResponseForbidden()

    beacon_list = Beacon.objects.all().order_by('beacon_id')
    paginator = Paginator(beacon_list, 10)

    # Try to get the page number
    page = request.GET.get('page', 1)
    try:
        beacons = paginator.page(page)
    except PageNotAnInteger:
        beacons = paginator.page(1)
    except EmptyPage:
        """Page number is out of range"""
        beacons = paginator.page(paginator.num_pages)

    context = {
        'email': request.user.email,
        'categories': StationCategory.objects.all(),
        'beacons': beacons
    }

    return render(request, 'app/beacon_list_page.html', context)


@login_required
def beacon_add_page(request):
    if not request.user.is_administrator():
        return HttpResponseForbidden()

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
def beacon_edit_page(request, pk):
    if not request.user.is_administrator():
        return HttpResponseForbidden()

    beacon = get_object_or_404(Beacon, pk=pk)

    if request.method == 'POST':
        form = BeaconForm(request.POST, instance=beacon)
        print(request.POST)
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
def beacon_delete_page(request, pk):
    if not request.user.is_administrator():
        return HttpResponseForbidden()

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

    if request.user.can(Permission.ADMIN):
        stations = Station.objects.all()
    else:
        stations = Station.objects.filter(owner_group=request.user.group)

    station_data = [
        {
            'id': station.id,
            'name': station.name,
            'primary_image': StationImage.objects.filter(
                station=station,
                is_primary=True
            ).first(),
            'category': station.category,
            'beacon': Beacon.objects.filter(
                station=station
            ).first()
        }
        for station in stations
    ]

    context = {
        'email': request.user.email,
        'stations': station_data,
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/station_list.html', context)


@login_required
def travelplan_list_page(request):
    context = {
        'categories': StationCategory.objects.all(),
        'email': request.user.email,
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
                'categories': StationCategory.objects.all(),
                'email': request.user.email,
                'travelplans': TravelPlan.objects.all()
            }

            return HttpResponseRedirect('/travelplans/')
    else:
        travelplan_form = PartialTravelPlanForm()

    context = {
        'categories': StationCategory.objects.all(),
        'email': request.user.email,
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

            if not json_order:
                for travelplan_station in TravelPlanStations.objects.filter(travelplan_id=pk):
                    travelplan_station.delete()

            else:
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

            context = {
                'categories': StationCategory.objects.all(),
                'email': request.user.email,
                'travelplans': TravelPlan.objects.all()
            }

            return HttpResponseRedirect('/travelplans/')
        form_data = travelplan_form.cleaned_data

    else:
        form_data = {
            'name': travelplan.name,
            'description': travelplan.description
        }

    travelplanstations = TravelPlanStations.objects.filter(
        travelplan_id=pk
    ).order_by('order')

    selected_stations_id = [
        travelplanstation.station_id
        for travelplanstation in travelplanstations
    ]

    selected_stations = [
        Station.objects.get(id=station_id)
        for station_id in selected_stations_id
    ]

    context = {
        'email': request.user.email,
        'stations': Station.objects.all(),
        'travelplan': travelplan,
        'travelplanstations': travelplanstations,
        'selected_stations': selected_stations,
        'form_data': form_data,
        'categories': StationCategory.objects.all()
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
def question_list_page(request):
    if request.user.is_administrator():
        stations = Station.objects.all()
    else:
        stations = Station.objects.filter(owner_group=request.user.group)

    station_questions = [
        {
            'station': station.name,
            'questions': station.question_set.all()
        }
        for station in stations
    ]
    station_questions.append(
        {
            'station': '(Not Linked)',
            'questions': Question.objects.filter(linked_station=None)
        }
    )
    context = {
        'station_questions': station_questions,
        'email': request.user.email,
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/question_list_page.html', context)


@login_required
def question_add_page(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            question = form.save()

            for i in range(1, 5):
                choice_name = 'choice{0}'.format(i)
                if data[choice_name]:
                    choice = Choice.objects.get_or_create(content=data[choice_name])[0]
                    is_answer = (choice_name == data['answer'])
                    QuestionChoice.objects.create(question=question, choice=choice, is_answer=is_answer)
            return HttpResponseRedirect('/questions/')
    else:
        form = QuestionForm()

    context = {
        'email': request.user.email,
        'categories': StationCategory.objects.all(),
        'form': form
    }
    return render(request, 'app/question_add_page.html', context)


@login_required
def question_edit_page(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            data = form.cleaned_data
            question = form.save()
            question.choices.clear()
            question.save()

            for i in range(1, 5):
                choice_name = 'choice{0}'.format(i)
                if data[choice_name]:
                    choice = Choice.objects.get_or_create(content=data[choice_name])[0]
                    is_answer = (choice_name == data['answer'])
                    QuestionChoice.objects.create(question=question, choice=choice, is_answer=is_answer)

            # Clear unused choices
            Choice.objects.filter(questionchoice__question=None).delete()

            return HttpResponseRedirect('/questions/')
    else:
        form = QuestionForm()

    choices = list(QuestionChoice.objects.filter(question=question))
    answer = ''
    for index, choice in enumerate(choices, 1):
        if choice.is_answer is True:
            answer = 'choice{0}'.format(index)

    form_data = {
        'content': question.content,
        'linked_station': question.linked_station,
        'choice1': choices[0].choice.content,
        'choice2': choices[1].choice.content,
        'choice3': choices[2].choice.content,
        'choice4': choices[3].choice.content,
        'answer': answer
    }

    if request.user.is_administrator():
        stations = Station.objects.all()
    else:
        stations = Station.objects.filter(owner_group=request.user.group)

    context = {
        'email': request.user.email,
        'categories': StationCategory.objects.all(),
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
