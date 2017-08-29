from django.conf.urls import url

from . import views


urlpatterns = [
    url('^signup/$', views.signup, name='signup'),
    url('^login/$', views.login, name='login'),
    url('^logout/$', views.logout, name='logout'),
    url('^get_all_rewards/$', views.get_all_rewards, name='Get All Reward'),
    url('^get_all_stations/$', views.get_all_stations, name='Get All Station')
]
