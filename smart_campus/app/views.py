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


import os
import random
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s: %(levelname)s : %(message)s', level=logging.INFO)

from .models import (
    User, Reward, Permission,
    Station, StationCategory,
    Beacon, StationImage, Question,
    UserReward, UserGroup,
    TravelPlan, Role
)
from .forms import (
    StationForm,
    CategoryForm,
    ManagerForm,
    PartialRewardForm,
    BeaconForm
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

    categories_data = [
        {
            'name': category.name,
        }
        for category in categories
    ]

    context = {'email': request.user.email, 'categories': categories_data}
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
            'beacon_name': station.beacon_set.first().name,
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
    for each_img in station_images:
        each_img.is_primary = False
        each_img.save()

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
            os.remove(img.image.path)
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
    """API for retrieving contents of all Stations"""
    print(request.get_host())
    data = [
        {
            'id': station.id,
            'name': station.name,
            'content': station.content,
            'category': str(station.category),
            'location': station.location.get_coords(),
            'image': {
                'primary':
                    'http://{0}{1}'.format(request.get_host(), StationImage.objects.filter(station=station, is_primary=True).first().image.url)
                    if StationImage.objects.filter(station=station, is_primary=True).exists()
                    else '',
                'others': ['http://{0}{1}'.format(request.get_host(), img.image.url)
                           for img in StationImage.objects.filter(station=station, is_primary=False)]
            }
        }
        for station in Station.objects.all()
    ]

    return JsonResponse(data={'data': data}, status=200, json_dumps_params={'ensure_ascii': False}, content_type='application/json; charset=utf-8')


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
    # POST a reward id and update the user data
    email = request.POST.get('email')
    reward_id = request.POST.get('reward_id')

    user = User.objects.filter(email=email).first()
    reward = Reward.objects.filter(id=reward_id).first()

    if not user or not reward:
        return HttpResponse('User or reward is not exitst', status=404)
    try:
        UserReward.objects.create(user=user, reward=reward)
    except ValueError:
        return HttpResponse('Cant Create The Relation', status=400)

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
    """add the category"""
    if request.method == 'POST':
        category_form = CategoryForm(request.POST)

        if category_form.is_valid():
            if request.user.can(Permission.ADMIN):
                stations = Station.objects.all()
            elif request.user.can(Permission.EDIT):
                stations = Station.objects.filter(
                    owner_group=request.user.group)
            else:
                return HttpResponseForbidden()

            category_form.save()
            context = {
                'name': category_form.cleaned_data['name'],
                'station_list': [{
                        'id': station.id,
                        'name': station.name,
                        'image_url': station.primary_image_url
                    }
                    for station in stations
                ],
                'categories': StationCategory.objects.all()
            }

            # TODO
            # add the specified category station list
            return HttpResponse('Success', status=200)
            # return render(request, 'station_list.html', context)
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
    # list all rewards

    context = {
        'email': request.user.email,
        'rewards': Reward.objects.all(),
        'categories': StationCategory.objects.all()
    }

    return render(request, 'app/reward_list_page.html', context)


@login_required
def reward_add_page(request):
    # add the reward
    if request.method == 'POST':
        reward_form = PartialRewardForm(request.POST, request.FILES)

        if reward_form.is_valid():
            reward_form.save()

            context = {
                'rewards': Reward.objects.all(),
                'email': request.user.email,
                'categories': StationCategory.objects.all()
            }
            # messages.info(request, 'Three credits remain in your account.')
            # return HttpResponse('Success', status=200)
            return render(request, 'app/reward_list_page.html', context)

    context = {
        'email': request.user.email,
        'categories': StationCategory.objects.all()
    }
    return render(request, 'app/reward_add_page.html', context)


@login_required
def manager_list_page(request):
    if not request.user.is_administrator():
        return HttpResponseForbidden()

    context = {
        'email': request.user.email,
        'managers': User.objects.exclude(role__name='User')
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
        'form': form
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
            manager = form.save(commit=False)
            manager.save()

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
        'form_data': form_data
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

    context = {
        'email': request.user.email,
        'beacons': Beacon.objects.all(),
        'categories': StationCategory.objects.all()
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
        'groups': UserGroup.objects.all(),
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
