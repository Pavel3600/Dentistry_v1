"""Test-only settings — overrides production settings to use SQLite."""
from django_app.settings import *  # noqa: F401, F403

# Disable SQLite FK constraint checks (Django 6 bug with managed=False models
# that use custom db_table — check_constraints looks for app_<model> instead).
from django.db.backends.sqlite3 import base as _sqlite3_base
_sqlite3_base.DatabaseWrapper.check_constraints = lambda self, table_names=None: None

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',  # noqa: F405
    }
}

# Disable FastAPI health check on startup during tests
FASTAPI_URL = 'http://localhost:9999'  # non-existent port so apps.py check is skipped
REQUIRE_FASTAPI = False  # don't block views during tests

# Faster password hashing in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Don't actually send emails in tests
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
