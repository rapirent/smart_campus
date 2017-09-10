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
    UserReward
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
    nickname = request.POST.get('nickname', '')

    if not email or not password:
        return HttpResponse('No email or password data', status=400)

    if User.objects.filter(email=email).exists():
        return HttpResponse('The email is already taken, try another!', status=400)

    try:
        User.objects.create_user(email, password, nickname)
    except ValueError as error:
        return HttpResponse('Email address not valid!', status=400)

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

    return HttpResponse('Login failure', status=401)


@csrf_exempt
@require_POST
def logout(request):
    """Logout API for APP users

    Handle logout requests from app

    """
    email = request.POST.get('email')
    request.user = User.objects.get(email=email)

    auth.logout(request)
    return HttpResponse('Logout success', status=200)


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
            return render(request, 'app/login.html')

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
    if request.user.can(Permission.ADMIN):
        stations = Station.objects.all()
    else:
        stations = Station.objects.filter(owner_group=request.user.group)

    station_data = [
        {
            'id': station.id,
            'name': station.name,
        }
        for station in stations
    ]

    context = {'email': request.user.email, 'stations': stations_data}
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

    return JsonResponse(data={'data': data}, status=200, json_dumps_params={'ensure_ascii': False}, content_type='application/json; charset=utf-8')


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
            'image': {
                'primary': 'http://{0}{1}'.format(request.get_host(), station.primary_image_url),
                'others': ['http://{0}/{1}'.format(request.get_host(), img.image.url)
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
        return HttpResponse('station or user not exist', status=400)

    questions = Question.objects.filter(linked_station=station)
    user_answered_questions = Question.objects.filter(user=user)

    # Get questions that the user hasn't answered yet
    questions_not_answered = questions.difference(user_answered_questions)

    if questions_not_answered.exists():
        # pick 1 question randomly
        question = random.sample(list(questions_not_answered), 1)[0]
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

    return HttpResponse('No more questions available to the user', status=404)


@csrf_exempt
@require_POST
def update_user_coins(request):
    coins = request.POST.get('coins')
    email = request.POST.get('email')

    user = User.objects.filter(email=email).first()

    if not user or not coins:
        return HttpResponse('User not exist or no coins data', status=400)

    try:
        user.earned_coins = coins
        user.save()
    except ValueError:
        return HttpResponse('Invalid input of coins', status=400)

    return JsonResponse(data={'message': 'Coins record of {0} successfully updated'.format(email), 'data': {'coins': user.earned_coins}}, status=200)


@csrf_exempt
@require_POST
def update_user_experience_point(request):
    experience_point = request.POST.get('experience_point')
    email = request.POST.get('email')

    user = User.objects.filter(email=email).first()

    if not user or not experience_point:
        return HttpResponse('User not exist or no experience_point data', status=400)

    try:
        user.experience_point = experience_point
        user.save()
    except ValueError:
        return HttpResponse('Invalid input of experience point', status=400)

    return JsonResponse(data={'message': 'Experience point record of {0} successfully updated'.format(email), 'data': {'experience_point': user.experience_point}}, status=200)


@csrf_exempt
@require_POST
def update_user_reward(request):
    # POST a reward id and update the user data
    email = request.POST.get('email')
    reward_id = request.POST.get('reward_id')

    user = User.objects.filter(email=email).first()
    reward = Reward.objects.filter(id=reward_id)

    if not user or not reward:
        return HttpResponse('User or reward is not exitst', status=404)
    try:
        # TODO
        user.add(reward)
        user.save()
    except ValueError:
        return HttpResponse('Invalid input of reward id', status=400)

    return JsonResponse({
            'status': 'true',
            'message': 'Success',
            'data': {
                reward: [reward.id for reward
                        in UserReward.objects.filter(user=user)]
            }
        },
        status=200
    )
