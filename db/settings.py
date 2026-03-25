import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

TEMPLATE_DIR = BASE_DIR / 'template'


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def csv_env(name, default=''):
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(',') if item.strip()]


def normalize_cloudinary_url(raw_value):
    value = (raw_value or '').strip()
    if not value:
        return ''

    if value.startswith('CLOUDINARY_URL='):
        value = value.split('=', 1)[1].strip()

    value = value.strip('"').strip("'").strip()
    value = value.replace('<', '').replace('>', '').strip()

    if value.lower().startswith('cloudinary://'):
        return value

    return ''


SANITIZED_CLOUDINARY_URL = normalize_cloudinary_url(os.getenv('CLOUDINARY_URL'))

if SANITIZED_CLOUDINARY_URL:
    os.environ['CLOUDINARY_URL'] = SANITIZED_CLOUDINARY_URL
else:
    os.environ.pop('CLOUDINARY_URL', None)


USE_CLOUDINARY = bool(
    SANITIZED_CLOUDINARY_URL or (
        os.getenv('CLOUDINARY_CLOUD_NAME')
        and os.getenv('CLOUDINARY_API_KEY')
        and os.getenv('CLOUDINARY_API_SECRET')
    )
)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-(w*@7afqwn04hs#s*j&-t1qt=js8ik8!wv*jlv$306rf2$(8h4',
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env_flag('DJANGO_DEBUG', default=True)

ALLOWED_HOSTS = csv_env('DJANGO_ALLOWED_HOSTS', default='127.0.0.1,localhost,.onrender.com')
CSRF_TRUSTED_ORIGINS = csv_env(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    default='https://*.onrender.com',
)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'account',
    'django_filters',
]

if USE_CLOUDINARY:
    INSTALLED_APPS += [
        'cloudinary_storage',
        'cloudinary',
    ]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
     'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'db.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'db.wsgi.application'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

database_url = os.getenv('DATABASE_URL')

if database_url:
    DATABASES = {
        'default': dj_database_url.parse(database_url, conn_max_age=600, ssl_require=False),
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

if USE_CLOUDINARY:
    STORAGES['default'] = {
        'BACKEND': 'cloudinary_storage.storage.MediaCloudinaryStorage',
    }
    CLOUDINARY_STORAGE = {
        'SECURE': True,
    }

    if os.getenv('CLOUDINARY_CLOUD_NAME') and os.getenv('CLOUDINARY_API_KEY') and os.getenv('CLOUDINARY_API_SECRET'):
        CLOUDINARY_STORAGE.update(
            {
                'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME'),
                'API_KEY': os.getenv('CLOUDINARY_API_KEY'),
                'API_SECRET': os.getenv('CLOUDINARY_API_SECRET'),
            }
        )

    if os.getenv('CLOUDINARY_STORAGE_PREFIX'):
        CLOUDINARY_STORAGE['PREFIX'] = os.getenv('CLOUDINARY_STORAGE_PREFIX').strip('/')
