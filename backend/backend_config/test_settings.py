from .settings import *  # noqa: F403,F401

from pathlib import Path


TEST_BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEST_DB_DIR = TEST_BASE_DIR / "frontend" / "src" / ".kcf_test_data"
TEST_DB_DIR.mkdir(parents=True, exist_ok=True)

DATABASES["default"] = {  # noqa: F405
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": TEST_DB_DIR / "test_db.sqlite3",
    "OPTIONS": {
        "timeout": 30,
    },
}

# Keep local test automation friction low.
DEBUG = True
BYPASS_USER_APPROVAL = True

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
