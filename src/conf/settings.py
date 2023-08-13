from pathlib import Path
from typing import Union

from .env import env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

DEBUG = env.debug
PROD = env.prod

if not PROD:
    SECRET_KEY = env.django_secret_key
else:
    SECRET_KEY = env.secrets['django_secret_key']

ALLOWED_HOSTS = env.allowed_hosts
CSRF_TRUSTED_ORIGINS = env.csrf_trusted_origins

# Application definition

INSTALLED_APPS = [
    # 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    # 'django.contrib.staticfiles',

    # 3rd party
    'storages',

    # local apps
    # 'example_app',
    'user_auth',
    'user_profiles',
    'publications',
    'transactions',
    'permissions',
    'utilities',
]

AUTH_USER_MODEL = 'user_profiles.UserProfile'
AUTHENTICATION_BACKENDS = ['user_auth.backend.EmailBackend']

if DEBUG:
    INSTALLED_APPS.append('django_extensions')

MIDDLEWARE = [
    'utilities.healthcheck_middleware.HealthCheckMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'transactions.clean_transactions.CleanTransactionMiddleWare',
]

ROOT_URLCONF = 'conf.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'conf.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASE_INFO: dict[str, Union[str, int]]
if not PROD:
    DATABASE_INFO = {
        'ENGINE': env.database_engine,
        'NAME': env.database_name,
        'USER': env.database_user,
        'PASSWORD': env.database_password,
        'HOST': env.database_host,
        'PORT': env.database_port
    }
else:
    DATABASE_INFO = {
        'ENGINE': env.database_engine,
        'NAME': env.secrets['db_name'],
        'USER': env.secrets['db_username'],
        'PASSWORD': env.secrets['db_password'],
        'HOST': env.secrets['db_host'],
        'PORT': env.secrets['db_port']
    }

DATABASES = {
    'default': DATABASE_INFO
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',  # noqa
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',  # noqa
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/
# We're serving directly from the fs by default.
# Change this if you want to use boto3

# STATIC_URL = '/static/'
# STATIC_ROOT = '/django/static'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not PROD:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    FRONTEND_URL = 'localhost:3000'
    EMAIL_DEFAULT_FROM = None
else:
    FRONTEND_URL = env.csrf_trusted_origins[0]
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env.secrets['email_host']
    EMAIL_PORT = env.secrets['email_port']
    EMAIL_HOST_USER = env.secrets['email_username']
    EMAIL_HOST_PASSWORD = env.secrets['email_password']
    EMAIL_DEFAULT_FROM = env.secrets['email_default_from']
    EMAIL_USE_TLS = env.email_use_tls

FINTOC_ACCOUNT: dict[str, str]
if not PROD:
    FINTOC_KEY = env.fintoc_key
    FINTOC_WEBHOOK_SECRET = env.fintoc_webhook_secret
    FINTOC_PAYMENT_URI = env.fintoc_payment_uri
    FINTOC_ACCOUNT = {
        'holder_id': env.fintoc_holder_id,
        'institution_id': env.fintoc_institution_id,
        'number': env.fintoc_number,
        'type': env.fintoc_type
    }
else:
    FINTOC_KEY = env.secrets['fintoc_key']
    FINTOC_WEBHOOK_SECRET = env.secrets['fintoc_webhook_secret']
    FINTOC_PAYMENT_URI = env.secrets['fintoc_payment_uri']
    FINTOC_ACCOUNT = {
        'holder_id': env.secrets['fintoc_holder_id'],
        'number': env.secrets['fintoc_number'],
        'type': env.secrets['fintoc_type'],
        'institution_id': env.secrets['fintoc_institution_id']
    }


if not PROD:
    MAX_FILE_SIZE = env.max_file_size
    MAX_FILE_NUMBER = env.max_file_number
else:
    MAX_FILE_SIZE = env.secrets['max_file_size']
    MAX_FILE_NUMBER = env.secrets['max_file_number']
    # aws settings
    AWS_ACCESS_KEY_ID = env.secrets['aws_access_key_id']
    AWS_SECRET_ACCESS_KEY = env.secrets['aws_access_key']
    AWS_STORAGE_BUCKET_NAME = env.secrets['s3_bucket_name']
    AWS_DEFAULT_ACL = None
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    # s3 public media settings
    PUBLIC_MEDIA_LOCATION = 'media'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
