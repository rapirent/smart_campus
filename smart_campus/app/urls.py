from django.conf.urls import url

from . import views


urlpatterns = [
    url('^signup/$', views.signup, name='signup'),
    url('^login/$', views.login, name='login'),
    url('^logout/$', views.logout, name='logout'),
    url('^get_all_rewards/$', views.get_all_rewards, name='Get All Reward'),
    url('^get_all_stations/$', views.get_all_stations, name='Get All Station'),
    url('^get_linked_stations/$', views.get_linked_stations, name='Get linked station'),
    url('^get_single_question/$', views.get_single_question, name='Get question'),
    url('^update_user_coins/$', views.update_user_coins, name='Update user coins'),
    url('^update_user_experience/$', views.update_user_experience, name='Update User Experience'),
    url('^update_user_reward/$', views.update_user_reward,
        name="Update User Reward")
]
