# Smart Campus

[![Build Status](https://travis-ci.org/rapirent/smart_campus.svg?branch=develop)](https://travis-ci.org/rapirent/smart_campus?branch=develop)
[![Coverage Status](https://coveralls.io/repos/github/rapirent/smart_campus/badge.svg?branch=develop)](https://coveralls.io/github/rapirent/smart_campus?branch=develop)

## Prerequistie
- Python 3
- postgres

### Install dependency

- dev

```sh
$ pip install -r requirements/dev.txt
```
## Setup and Run
### Develop: Use local settings file
Define your own `local_settings.py` under `settings/`
#### Runserver
```sh
python manage.py runserver --settings=smart_campus.settings.local_settings
```
### Production: Setup Envrionment Variables
- `SECRET_KEY`
- `POSTGRESQL_NAME`
- `POSTGRESQL_USER`
- `POSTGRESQL_PASSWORD`
- `POSTGRESQL_HOST`
- `POSTGRESQL_PORT`
- `DJANGO_SETTINGS_MODULE`

```sh
export SECRET_KEY='Some hard to guess value'
export POSTGRESQL_NAME='db_name'
export POSTGRESQL_USER='user_name'
export POSTGRESQL_PASSWORD='user_pwd'
export POSTGRESQL_HOST='db_host'
export POSTGRESQL_PORT='db_port'
export DJANGO_SETTINGS_MODULE="smart_campus.settings.production"
```
#### Nginx, uwsgi setup
- [Setting up Django and your web server with uWSGI and nginx](http://uwsgi-docs.readthedocs.io/en/latest/tutorials/Django_and_nginx.html)

#### Run uwsgi
##### Start
```sh
uwsgi --ini server-settings/smart_campus.ini
```

##### Stop
```sh
sudo killall -s INT uwsgi
```

## Testing

### Run Test
```sh
$ pytest
```

Note that test should be run in root directory instead of `smart_campus`.
