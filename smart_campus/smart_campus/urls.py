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
    url(r'^admin/', admin.site.urls),
    url(r'^smart_campus/', include('app.urls')),
    url(r'^login/$', app.views.login_page, name='Login Page'),
    url(r'^logout/$', app.views.logout_page, name='Logout Page'),
    url(r'^$', app.views.index, name='index'),
    url(r'^stations/$', app.views.station_list_page, name='Station List Page'),
    url(r'^stations/new/$', app.views.station_new_page, name='Add Station Page'),
    url(r'^stations/(?P<pk>\d+)/edit/$', app.views.station_edit_page, name='Edit Station Page'),
    url(r'^add_category/$', app.views.category_add_page,
        name='Category Add Page')
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )