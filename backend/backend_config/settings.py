import os
from datetime import timedelta
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent


def split_env(name, default=''):
    return [value.strip() for value in os.getenv(name, default).split(',') if value.strip()]

SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'kwetu-care-local-dev-secret-key-please-change-in-production-2026',
)
DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() == 'true'

ALLOWED_HOSTS = split_env('DJANGO_ALLOWED_HOSTS')
railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
if railway_domain:
    ALLOWED_HOSTS.append(railway_domain)
if DEBUG and not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend_config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend_config.wsgi.application'
ASGI_APPLICATION = 'backend_config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 30,
        },
    }
}

if os.getenv('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.config(
        conn_max_age=600,
        ssl_require=os.getenv('DATABASE_SSL_REQUIRE', 'false').lower() == 'true',
    )

AUTH_PASSWORD_VALIDATORS = []
AUTH_USER_MODEL = 'core.User'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Local testing helper: when True, signup auto-approves users and approval checks are bypassed.
BYPASS_USER_APPROVAL = os.getenv('BYPASS_USER_APPROVAL', 'true').lower() == 'true'

DEFAULT_FRONTEND_ORIGINS = [
    'https://kwetu-care-foundation-i6vf7j1wj-imbukwa1s-projects.vercel.app',
]

CORS_ALLOWED_ORIGINS = split_env('CORS_ALLOWED_ORIGINS') or DEFAULT_FRONTEND_ORIGINS
CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'true').lower() == 'true'
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = split_env('CSRF_TRUSTED_ORIGINS') or DEFAULT_FRONTEND_ORIGINS

# For production, replace with allowed origin list
# CORS_ALLOWED_ORIGINS = [
#     'http://localhost:3000',
#     'https://your-frontend-domain.com',
# ]
