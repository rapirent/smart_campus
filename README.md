# Smart Campus

[![Build Status](https://travis-ci.org/rapirent/smart_campus.svg?branch=develop)](https://travis-ci.org/rapirent/smart_campus?branch=develop)
[![Coverage Status](https://coveralls.io/repos/github/rapirent/smart_campus/badge.svg?branch=develop)](https://coveralls.io/github/rapirent/smart_campus?branch=develop)

## Prerequistie
- Python 3
- PostgreSQL
- PostGIS

## Table of Content
1. [Install Software & Configure Environemnt](#sec1)
2. [Setup Setting Files](#sec2)
3. [Run Server](#sec3)
4. [Setup default data](#sec4)
5. [Testing](#sec5)

<a name="sec1"></a>
## 1. Install Software & Configure Environemnt
### Software Installation
- [Python3](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org)
- [PostGIS](http://postgis.net)
- [Virtualenv](https://virtualenv.pypa.io/en/stable/)

### Environment Setup
1. Create virtual enviroment

	```sh
	$ virtualenv -p `which python3` venv
	```

2. Start up virtual environment

	```sh
	$ source venv/bin/activate
	```

	To exit virtual environment

	```sh
	$ deactivate
	```

3. Install python dependencies

	- dev

	```sh
	$ pip install -r requirements/dev.txt
	```

4. Set system locale to utf8

	```sh
	export LC_ALL='en_US.utf8'
	```

<a name='sec2'></a>
## 2. Setup settings files

### Development
Define your own `local_settings.py` under `smart_campus/smart_campus/settings/`  
This file will be and should be ignored by git.  
  
The follwoing variables MUST be set up in the setting file.
  
- `SECRET_KEY`
- `DATABASES`

e.g.

```python
# smart_campus/smart_campus/settings/local_settings.py

from .base import *


SECRET_KEY = 'This is the secret key'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'db_name',
        'USER': 'db_user',
        'PASSWORD': 'db_pwd',
        'HOST': 'localhost',
        'PORT': '5432',
    },
}
```

### Production

The following envrionment variables MUST be setup.

- `SECRET_KEY`
- `POSTGRESQL_NAME`
- `POSTGRESQL_USER`
- `POSTGRESQL_PASSWORD`
- `POSTGRESQL_HOST`
- `POSTGRESQL_PORT`
- `DJANGO_SETTINGS_MODULE`

e.g.

```sh
$ export SECRET_KEY='Some hard to guess value'
$ export POSTGRESQL_NAME='db_name'
$ export POSTGRESQL_USER='user_name'
$ export POSTGRESQL_PASSWORD='user_pwd'
$ export POSTGRESQL_HOST='db_host'
$ export POSTGRESQL_PORT='db_port'
$ export DJANGO_SETTINGS_MODULE="smart_campus.settings.production"
```

### Setup Mail Server (Needed to be done in each setting files)

Setup the mail user & password (using gmail in default) in settings/settings.py
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`

Note that you will have to enable 'insecure access' in your gmail account.

<a name='sec3'></a>
## 3. Runserver

### Development
```sh
python manage.py runserver --settings=smart_campus.settings.local_settings
```

### Production

#### Nginx, uwsgi setup
- [Setting up Django and your web server with uWSGI and nginx](http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html)
- Put your nginx settings file *.conf in /etc/nginx/sites-enabled/

#### Run uwsgi
Run uWSGI as root, but be sure to drop privileges with the uid and gid options in *.ini settings file
##### Start
```sh
$ uwsgi --ini server-settings/smart_campus.ini
```

##### Stop
```sh
$ sudo killall -s INT uwsgi
```
##### View log
```sh
$ sudo tail -f /var/log/smartcampus/smartcampus.log
```

<a name="sec4"></a>
## 4. Setup default data

```
$ cd smart_campus
$ pwd
# smart_campus
```

### Initial Default Roles

```sh
$ python3 manage.py initroles
```

### Create Super User
```sh
$ python3 manage.py initroles
```

### Insert Default Beacon Data
```sh
$ python3 manage.py load_beacon_data [file.xls]
```

<a name="sec5"></a>
## 5. Testing

### Run Test
```sh
$ pytest
```

Note that test should be run in root directory instead of `smart_campus`.

## [API Document Site](https://rapirent.github.io/smart_campus/index.html)

## LICENS
