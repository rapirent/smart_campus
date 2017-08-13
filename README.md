# Smart Campus

## Prerequistie
- Python 3
- postgres

### Install dependency

- dev

```sh
$ pip install -r requirements/dev.txt
```

### Setup Envrionment Variables
- `SECRET_KEY`
- `POSTGRESQL_NAME`
- `POSTGRESQL_USER`
- `POSTGRESQL_PASSWORD`
- `POSTGRESQL_HOST`
- `POSTGRESQL_PORT`

```sh
export SECRET_KEY='Some hard to guess value'
export POSTGRESQL_NAME='db_name'
export POSTGRESQL_USER='user_name'
export POSTGRESQL_PASSWORD='user_pwd'
export POSTGRESQL_HOST='db_host'
export POSTGRESQL_PORT='db_port'
```


## Testing

### Run Test
```sh
$ pytest
```

Note that test should be run in root directory instead of `smart_campus`.
