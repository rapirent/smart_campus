from django.conf.urls import url

from . import views


urlpatterns = [
    url('^signup/$', views.signup, name='Signup'),
    url('^login/$', views.login, name='Login'),
    url('^logout/$', views.logout, name='Logout'),
    url('^get_all_rewards/$', views.get_all_rewards, name='Get All Reward'),
    url('^get_all_stations/$', views.get_all_stations, name='Get All Station'),
    url('^get_linked_stations/$', views.get_linked_stations,
        name='Get Linked Station'),
    url('^update_user_coins/$', views.update_user_coins,
        name='Update User Coins'),
    url('^update_user_experience_point/$', views.update_user_experience_point,
        name='Update User Experience Point'),
    url('^add_user_favorite_stations/$', views.add_user_favorite_stations,
        name='Add User Favorite Stations'),
    url('^remove_user_favorite_stations/$',
        views.remove_user_favorite_stations,
        name='Remove User Favorite Stations'),
    url('^get_all_travel_plans/$', views.get_all_travel_plans,
        name='Get All Travel plans'),
    url('^add_user_reward/$', views.add_user_reward, name='Add User Reward'),
    url('^get_unanswered_question/$', views.get_unanswered_question,
        name='Get Unanswered questsion'),
    url('^add_answered_question/$', views.add_answered_question,
        name='Add Answered Question'),
    url('^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='Activate'),
    url('^reset_password/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.reset_password_page, name='Reset Password Page'),
    url('^reset_password/(?P<email>[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})/$',
        views.reset_password, name="Reset Password"),
    url('^resend_activation/(?P<email>[\w.%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})/$',
        views.resend_activation, name="Resend Activation Email")
]
