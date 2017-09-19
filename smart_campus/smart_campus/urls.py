"""smart_campus URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

import app


urlpatterns = [
    url(r'^smart_campus/', include('app.urls')),
    url(r'^login/$', app.views.login_page, name='Login Page'),
    url(r'^logout/$', app.views.logout_page, name='Logout Page'),
    url(r'^$', app.views.index, name='index'),

    # Stations
    url(r'^stations/$', app.views.station_list_page, name='Station List Page'),
    url(r'^stations/category/(?P<pk>\d+)/$', app.views.station_list_by_category_page, name='Station List By Category Page'),
    url(r'^stations/new/$', app.views.station_new_page, name='Add Station Page'),
    url(r'^stations/(?P<pk>\d+)/edit/$', app.views.station_edit_page, name='Edit Station Page'),
    url(r'^station_image/(?P<pk>\d+)/set_primary/$', app.views.set_primary_station_image, name='Set Primary Station Image'),
    url(r'^station_image/(?P<pk>\d+)/delete/$', app.views.delete_station_image, name='Delete Station Image'),
    url(r'^stations/(?P<pk>\d+)/delete/$', app.views.station_delete_page,
        name='Delete Station Page'),

    # Categories
    url(r'^add_category/$', app.views.category_add_page,
        name='Category Add Page'),

    # Rewards
    url(r'rewards/$', app.views.reward_list_page,
        name='Reward List Page'),
    url(r'rewards/new/$', app.views.reward_add_page,
        name='Reward Add Page'),
    url(r'rewards/(?P<pk>\d+)/edit$', app.views.reward_edit_page,
        name='Reward Edit Page'),
    url(r'rewards/(?P<pk>\d+)/delete$', app.views.reward_delete_page,
        name='Reward Delete Page'),

    # Managers
    url(r'^managers/$', app.views.manager_list_page,
        name='Manager List Page'),
    url(r'^managers/new/$', app.views.manager_add_page,
        name='Manager Add Page'),
    url(r'^managers/(?P<pk>[^/]+)/edit/$', app.views.manager_edit_page,
        name='Manager Edit Page'),
    url(r'^managers/(?P<pk>[^/]+)/delete/$', app.views.manager_delete_page,
        name='Manager Delete Page'),

    # Beacons
    url(r'^beacons/$', app.views.beacon_list_page,
        name='Beacon List Page'),
    url(r'^beacons/new/$', app.views.beacon_add_page,
        name='Beacon Add Page'),
    url(r'^beacons/(?P<pk>[^/]+)/edit/$', app.views.beacon_edit_page,
        name='Beacon Edit Page'),
    url(r'^beacons/(?P<pk>[^/]+)/delete/$', app.views.beacon_delete_page,
        name='Beacon Delete Page'),
    url(r'^travelplans/$', app.views.travelplan_list_page,
        name='TravelPlan List Page'),
    url(r'^travelplans/new$', app.views.travelplan_add_page,
        name='TravelPlan Add Page'),
    url(r'^travelplans/(?P<pk>\d+)/edit/$', app.views.travelplan_edit_page,
        name='TravelPlan Edit Page'),
    url(r'^travelplans/(?P<pk>\d+)/delete/$',
        app.views.travelplan_delete_page,
        name='TravelPlan Delete Page'),

    # Questions
    url(r'^questions/$', app.views.question_list_page,
        name='Question List Page'),
    url(r'^questions/new/$', app.views.question_add_page,
        name='Question Add Page'),
    url(r'^questions/(?P<pk>\d+)/edit/$', app.views.question_edit_page,
        name='Question Edit Page'),
    url(r'^questions/(?P<pk>\d+)/delete/$', app.views.question_delete_page,
        name='Question Delete Page')
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
