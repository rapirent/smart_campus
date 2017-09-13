from django.conf.urls import url

from . import views


urlpatterns = [
    url('^signup/$', views.signup, name='Signup'),
    url('^login/$', views.login, name='Login'),
    url('^logout/$', views.logout, name='Logout'),
    url('^get_all_rewards/$', views.get_all_rewards, name='Get all reward'),
    url('^get_all_stations/$', views.get_all_stations, name='Get all station'),
    url('^get_linked_stations/$', views.get_linked_stations, name='Get linked station'),
    url('^get_unanswered_question/$', views.get_unanswered_question, name='Get question'),
    url('^update_user_coins/$', views.update_user_coins, name='Update user coins'),
    url('^update_user_experience_point/$', views.update_user_experience_point, name='Update user experience point'),
    url('^add_user_favorite_stations/$', views.add_user_favorite_stations, name='Add user favorite stations'),
    url('^remove_user_favorite_stations/$', views.remove_user_favorite_stations, name='Remove user favorite stations'),
    url('^get_all_travel_plans/$', views.get_all_travel_plans, name='Get all travel plans'),
    url(r'^add_user_reward/$',
        views.add_user_reward,
        name="Add User Reward"
        )
]
