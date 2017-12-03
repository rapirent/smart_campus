from .base import *

DEBUG = True

SECRET_KEY = get_env_variable('SECRET_KEY')

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': get_env_variable('POSTGRESQL_NAME'),
        'USER': get_env_variable('POSTGRESQL_USER'),
        'PASSWORD': get_env_variable('POSTGRESQL_PASSWORD'),
        'HOST': get_env_variable('POSTGRESQL_HOST'),
        'PORT':  get_env_variable('POSTGRESQL_PORT'),
    },
}

MEDIA_ROOT = '/var/www/smartcampus.csie.ncku.edu.tw/media'
