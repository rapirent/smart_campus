import pytest
from django.core.exceptions import ImproperlyConfigured

from smart_campus.settings import get_env_variable


class TestGetEnvVariable:
    def test_get_secret_key_succeeded(self, monkeypatch):
        monkeypatch.setenv('SECRET_KEY', 'test secret key')
        get_env_variable('SECRET_KEY')


    def test_get_no_such_env_variable_failed(self):
        with pytest.raises(ImproperlyConfigured):
            get_env_variable('NO_SUCH_ENV_VARIABLE')
